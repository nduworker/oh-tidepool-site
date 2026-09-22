"""Read-only public contract validation; mirrored in the private publisher."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator, FormatChecker


SCHEMAS = Path(__file__).resolve().parent
DIGEST = re.compile(r"^[a-f0-9]{64}$")
MEDIA_NAME = re.compile(r"^(?P<asset_id>[a-z0-9]+(?:-[a-z0-9]+)*)-v(?P<revision>[1-9][0-9]*)\.webp$")


class ContractError(ValueError):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def revision(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"JSON: duplicate key {key!r}")
        result[key] = value
    return result


def decode_json(data: str | bytes) -> dict:
    def reject_constant(value: str) -> None:
        raise ContractError(f"JSON: non-finite number {value}")

    try:
        value = json.loads(data, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (ValueError, UnicodeError) as error:
        raise ContractError(f"JSON: {error}") from error
    require(isinstance(value, dict), "JSON", "expected an object")
    return value


def read_json(filename: Path) -> dict:
    try:
        return decode_json(filename.read_bytes())
    except OSError as error:
        raise ContractError(f"{filename.name}: {error.strerror}") from error


def require(condition: bool, field: str, message: str) -> None:
    if not condition:
        raise ContractError(f"{field}: {message}")


def instant(value: str, field: str) -> datetime:
    require(isinstance(value, str) and bool(re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value
    )), field, "expected an ISO-8601 UTC instant ending in Z")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractError(f"{field}: invalid date/time") from error


def https_url(value: str, field: str) -> None:
    try:
        parts = urlsplit(value)
        valid = (parts.scheme == "https" and parts.hostname and not parts.username
                 and not parts.password and parts.port in (None, 443)
                 and not parts.fragment and not re.search(r"[\s\\]", value))
    except ValueError:
        valid = False
    require(bool(valid), field, "expected a credential-free HTTPS URL")


def schema_validate(value: dict, name: str, schemas: Path = SCHEMAS) -> None:
    schema = read_json(schemas / f"{name}.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(value), key=lambda error: str(list(error.absolute_path)))
    if errors:
        error = errors[0]
        field = ".".join(str(part) for part in error.absolute_path)
        raise ContractError(f"{name}.{field or '$'}: {error.message}")


def authority_for(source: dict, policy: dict) -> dict | None:
    url = urlsplit(source["url"])
    for authority in policy["authorities"]:
        if source["publisher"] != authority["publisher"]:
            continue
        for prefix in authority["url_prefixes"]:
            allowed = urlsplit(prefix)
            if (url.scheme == "https" and url.hostname == allowed.hostname
                    and url.path.startswith(allowed.path) and url.port in (None, 443)):
                if unquote(url.path) != url.path or any(segment in (".", "..") for segment in url.path.split("/")):
                    continue
                return authority
    return None


def validate_daily(value: dict, schemas: Path = SCHEMAS) -> None:
    schema_validate(value, "daily-conditions", schemas)
    policy = read_json(schemas / "catalog-policy.json")
    generated = instant(value["generated_at"], "daily.generated_at")
    published = instant(value["published_at"], "daily.published_at")
    expires = instant(value["expires_at"], "daily.expires_at")
    require(generated <= published < expires, "daily.expires_at", "require generated_at <= published_at < expires_at")
    require(expires - generated <= timedelta(days=3), "daily.expires_at", "must expire within three days")
    seen = set()
    for position, location in enumerate(value["locations"]):
        field = f"daily.locations[{position}]"
        identifier = location["location_id"]
        require(identifier in policy["location_ids"], field + ".location_id", "unknown catalog location")
        require(identifier not in seen, field + ".location_id", "duplicate location")
        seen.add(identifier)
        weather = location["weather"]
        observed = instant(weather["observed_at"], field + ".weather.observed_at")
        require(observed <= published, field + ".weather.observed_at", "cannot be after publication")
        try:
            date.fromisoformat(weather["forecast_date_local"])
            ZoneInfo(weather["forecast_time_zone"])
        except (ValueError, ZoneInfoNotFoundError) as error:
            raise ContractError(f"{field}.weather: invalid local date or IANA timezone") from error
        low, high = weather.get("temperature_low_f"), weather.get("temperature_high_f")
        require(low is None or high is None or low <= high, field + ".weather", "low cannot exceed high")
        if "daily_rank" in location:
            validate_rank(location["daily_rank"], field + ".daily_rank")
    require(not value["locations"] or bool(value["sources"]), "daily.sources", "weather requires attribution")
    for position, source in enumerate(value["sources"]):
        field = f"daily.sources[{position}]"
        https_url(source["url"], field + ".url")
        require(instant(source["retrieved_at"], field + ".retrieved_at") <= published,
                field + ".retrieved_at", "cannot be after publication")
    updates = value.get("local_updates", [])
    # Schema 3 is schema 2 plus the daily rank, so it carries updates too. A
    # `== 2` test here would have rejected the first briefing that had both a
    # rank and an official notice — the exact document the news agent publishes.
    require(value["schema_version"] in (2, 3) or not updates, "daily.local_updates",
            "schema version 1 carries no local updates")
    seen_updates = set()
    for position, update in enumerate(updates):
        field = f"daily.local_updates[{position}]"
        require(update["id"] not in seen_updates, field + ".id", "duplicate event")
        seen_updates.add(update["id"])
        require(set(update["affected_location_ids"]).issubset(policy["location_ids"]),
                field + ".affected_location_ids", "unknown catalog location")
        observed = instant(update["observed_at"], field + ".observed_at")
        released = instant(update["published_at"], field + ".published_at")
        ends = instant(update["expires_at"], field + ".expires_at")
        require(observed <= published and released <= published < ends <= expires,
                field + ".expires_at", "invalid effective interval or expiry exceeds document expiry")
        source = update["source"]
        https_url(source["url"], field + ".source.url")
        checked = instant(source["retrieved_at"], field + ".source.retrieved_at")
        require(released <= checked <= published, field + ".source.retrieved_at", "outside publication interval")
        authority = authority_for(source, policy)
        require(authority is not None, field + ".source", "publisher/URL is not an allowlisted authority")
        require(set(update["affected_location_ids"]).issubset(authority["location_ids"]),
                field + ".affected_location_ids", "outside this authority's reviewed geography")
        if update["impact"] != "context_only":
            require(authority["tier"] == "A" and update["category"] in authority["gate_categories"],
                    field + ".impact", "only Tier A operational evidence can gate recommendations")
            require(update["verification"] == "official" and update["status"] == "active",
                    field + ".impact", "a gate requires an active official notice")
            require(bool((update.get("official_guidance") or "").strip()),
                    field + ".official_guidance", "official guidance required")
            official_status = update.get("official_status")
            require(isinstance(official_status, str) and
                    authority["status_impacts"].get(official_status) == update["impact"],
                    field + ".official_status", "explicit agency status must support impact")


def validate_rank(value: dict, field: str) -> None:
    """Require a daily rank to agree with the inputs published beside it.

    A rank is only worth showing if it cannot contradict itself, so these rules
    are re-checked at the contract boundary rather than trusted from whichever
    generator produced it. They encode the safe defaults: a rank may never claim
    the best level from incomplete inputs, and it may never carry an official
    cap.
    """
    level = value["level"]
    inputs = value["inputs"]
    best_low = inputs["best_usable_low_feet"]
    precip = inputs["precipitation_probability_max"]
    gusts = inputs["wind_gusts_mph"]

    # A notice expires on its own clock, so a cap baked into a published rank
    # would outlive the notice that justified it and could not be lifted until
    # the whole briefing was rebuilt. A base rank must therefore be uncapped;
    # the app applies a current, location-matched notice at display time.
    require(
        not inputs["official_impacts"],
        field + ".inputs.official_impacts",
        "a published rank must not embed an expiring notice cap",
    )
    require(
        level != "good" or best_low is not None,
        field + ".level", "a good day must name the usable low tide that makes it good",
    )
    require(
        level != "good" or (precip is not None and gusts is not None),
        field + ".level", "a good day must not come from incomplete weather inputs",
    )
    require(
        inputs["tide_data_available"] or level != "poor",
        field + ".level",
        "a poor day must have had tide extremes to judge it by; a provider gap is not a verdict",
    )
    require(
        inputs["tide_data_available"] or level == "fair",
        field + ".level",
        "without tide extremes the day may only be presented as fair, not as a verdict either way",
    )


def validate_media(value: dict, schemas: Path = SCHEMAS) -> None:
    schema_validate(value, "media", schemas)
    instant(value["generated_at"], "media.generated_at")
    policy = read_json(schemas / "catalog-policy.json")
    require(value["revision"] == revision(value["assets"]), "media.revision", "does not hash the assets dictionary")
    for identifier, asset in value["assets"].items():
        field = f"media.assets.{identifier}"
        require(identifier in policy["assets"], field, "unknown catalog asset")
        expected = f"media/{identifier}-v{asset['revision']}.webp"
        require(asset["path"] == expected and MEDIA_NAME.fullmatch(expected[6:]) is not None,
                field + ".path", "unsafe path or filename/revision mismatch")
        require(asset["revision"] == policy["assets"][identifier], field + ".revision", "does not match reviewed catalog")


def validate_index(value: dict, schemas: Path = SCHEMAS) -> None:
    schema_validate(value, "index", schemas)
    instant(value["generated_at"], "index.generated_at")
    expected = revision({key: value[key] for key in ("media_revision", "conditions_revision")})
    require(value["revision"] == expected, "index.revision", "does not hash component revisions")


def validate_documents(root: Path, schemas: Path = SCHEMAS) -> None:
    index = read_json(root / "data/index.json")
    media = read_json(root / "data/media.json")
    validate_index(index, schemas)
    validate_media(media, schemas)
    require(index["media_revision"] == media["revision"], "index.media_revision", "does not match media.revision")
    daily_path = root / "data/daily-conditions.json"
    if daily_path.exists():
        daily = read_json(daily_path)
        validate_daily(daily, schemas)
        require(index["conditions_revision"] == daily["revision"], "index.conditions_revision", "does not match daily.revision")
    else:
        require(index["conditions_revision"] is None, "index.conditions_revision", "must be null when daily file is absent")
