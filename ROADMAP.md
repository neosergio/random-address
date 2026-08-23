# Roadmap

Work that has been considered and deliberately deferred, with the reason. This is not a promise of
dates or of delivery; it is a record so that the same ground is not re-covered from scratch, and so
that a deferred decision is visible rather than lost in a pull request comment.

Requests for specific cities, states or postal codes do not belong here. Those go to
[GitHub Issues](https://github.com/neosergio/random-address/issues), which is the workflow the README
describes, and they are added gradually to keep the package small.

## A `count` subcommand for the CLI

`count()` landed in 2.1.1 as a Python function only. The CLI already has a `summary` subcommand, so
`random-address count --state CA` is the obvious companion, and the argument parsing for `--state`,
`--city` and `--postal-code` already exists on the `get` subcommand.

Deferred because 2.1.1 was a patch release. Growing the command line surface changes what the tool
looks like to somebody reading `--help`, which is a minor-release decision rather than a patch one.

## Broader geographic coverage

The dataset holds 20 states after 2.1.1. Thirty-one are still unrepresented: DE HI IA ID IL IN KS LA
ME MI MN MO MS MT ND NE NH NJ NM NV NY OH PA RI SC SD UT WA WI WV WY.

This is gated on licensing, not on effort. Every address here is public domain, which is the one
promise the library makes, and OpenAddresses is the ceiling on what can be added. Two obstacles come
up repeatedly:

- **Attribution-required sources are unusable.** Utah's statewide source is otherwise ideal — 1.5
  million rows, complete postal codes — but it is CC BY 4.0 with `attribution: true`. Boise is the
  same. Share-alike sources (ODbL, and Portland Metro's RLIS) are out for the same reason.
- **Most current sources declare no license at all.** OpenAddresses' schema-2 sources frequently
  carry no `license` block, which reports as `false` in the job metadata. That includes several
  large, high-quality candidates: `us/ny/statewide`, `us/il/cook`, `us/nj/statewide`,
  `us/pa/allegheny`, `us/mn/hennepin`, `us/oh/city_of_columbus`, `us/de/statewide`,
  `us/nd/statewide`, `us/ks/statewide`. Absence of a license is *unknown*, not *public domain*, so
  using them means checking each upstream publisher's terms by hand first.

Texas was imported from `us/tx/statewide` (CC0) despite being 337 MB compressed and roughly 2.5 GB
uncompressed. `_read_features` reads a source fully into memory, so that file had to be narrowed to
the target cities by streaming before the ingest script could touch it. Any future statewide source
of that size needs the same treatment, or `_read_features` needs to stream.

## Unifying the two version declarations

The version is written twice, in `pyproject.toml` and in `src/random_address/__init__.py`. The
duplication is intentional and guarded: `publish.yml` fails a release unless the git tag, the
pyproject version and `__version__` all agree.

Collapsing it — setuptools `dynamic = ["version"]` reading `random_address.__version__` — means
rewriting that guard, since two of the three values it compares would become the same value and the
check would weaken. Worth doing, but not inside a patch release.

## Attribution lists Hawaii, but there are no Hawaii addresses

The README credits *City of Honolulu (HI)* under Attribution, and the dataset contains no HI records.
Most likely a leftover: 2.1.0 removed twenty records that had no city, and earlier releases removed
others.

Left alone deliberately. Editing an attribution list is a statement about provenance, and it should
be corrected by someone who knows whether those records were removed or never shipped — not silently,
as a side effect of an unrelated release.

## The leading-directional rule misfires on suffix-shaped street names

`normalize_street` leaves a leading directional unexpanded when the next token is a word that also
appears as a spelled-out street suffix. `SE MEADOW CT` normalized to `Se Meadow Court` rather than
`Southeast Meadow Court`, because `Meadow` is the expansion of `MDW`; `SW GARDEN PL` failed the same
way through `GDN`. Two Oregon records shipped like that in 2.1.1 and were corrected by hand. The next
import from a source that abbreviates directionals will reintroduce it.

The guard exists for a real reason — Washington DC has streets named after letters, so `S ST NW` must
stay `S Street Northwest` — and it is not safe to simply drop. Replacing the word test with a
position test (`suffix_at != 1`) looks right and is wrong: on the already-normalized `S Street
Northwest` the trailing `Northwest` is no longer recognized as a directional, so the suffix position
shifts and the rule corrupts three DC records into `South Street Northwest`. Any fix has to treat
spelled-out directionals as directionals when locating the suffix, and has to be checked against both
the raw and the already-normalized form of the same address.

## A stale comment in the ingest script

`ROUTE_PREFIXES` and the docstring of `_preserved` in `data/add_addresses.py` both refer to a
`_is_dotted_initialism` helper that does not exist. Dotted forms such as `U.S. 5` are actually handled
by the `character in ".&"` check inside `_preserved`.

Purely cosmetic, and it touches the normalizer, which is the single most delicate part of the ingest
path — the 2.1.0 changelog lists six separate street names it had corrupted. A comment fix is not
worth re-opening that file during a release focused on something else.
