"""Retired benchmark entry point; intentionally imports no providers or config."""
import sys


def main():
    print(
        "The legacy provider benchmark is unavailable in the supported profile. "
        "See docs/performance_tester.md. No configuration was loaded or provider called.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
