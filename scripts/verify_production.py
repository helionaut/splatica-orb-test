#!/usr/bin/env python3

from __future__ import annotations

import argparse
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-url", required=True)
    parser.add_argument("--expected-marker", default="splatica-orb-test")
    args = parser.parse_args()

    if not args.artifact_url:
        raise SystemExit("Pass --artifact-url with a published report or results URL.")

    try:
        with urlopen(args.artifact_url) as response:
            body = response.read().decode("utf-8", errors="replace")
            if response.status != 200:
                raise SystemExit(
                    f"Expected HTTP 200 from {args.artifact_url}, got {response.status}."
                )
    except HTTPError as error:
        raise SystemExit(f"HTTP verification failed: {error}") from error
    except URLError as error:
        raise SystemExit(f"URL verification failed: {error}") from error

    if args.expected_marker not in body:
        raise SystemExit(
            f'Expected "{args.expected_marker}" to appear in {args.artifact_url}.'
        )

    print(f"Verified production artifact at {args.artifact_url}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
