# Roadmap

Work that has been considered and deliberately deferred, with the reason. This is not a promise of
dates or of delivery; it is a record so that the same ground is not re-covered from scratch, and so
that a deferred decision is visible rather than lost in a pull request comment.

Requests for specific cities, states or postal codes do not belong here. Those go to
[GitHub Issues](https://github.com/neosergio/random-address/issues), which is the workflow the README
describes, and they are added gradually to keep the package small.

## 2.3.0: even out the states

The next release, planned for a few weeks after 2.2.0, once there is a sense of how the community
uses it. Until then no further releases are planned. It is a data-only release: no API changes.

2.2.0 left the dataset uneven. Thirteen states hold 50 addresses each (ID, IL, IN, LA, MN, NC, NM,
OH, OR, PA, SC, TX, VA), while the other sixteen hold between about 160 and 330. Count is not the
only gap: Connecticut has 196 addresses but only 2 cities and 3 postal codes, and Virginia's 50 are
all in Arlington. For a test, a hundred addresses spread over five cities are worth more than two
hundred in one neighbourhood.

The plan, balancing rather than growing for its own sake, because the package is meant to stay light:

- **A floor of 150 addresses per state.** States already above it keep what they have. Nothing is
  removed: a user's test may depend on a particular postal code.
- **A spread within each state:** at least 5 cities where the sources allow it, and
  `--per-postal-code` so no postal code dominates.
- **Only sources already verified as public domain.** The nine 2.2.0 sources are listed under
  Attribution in the README; the earlier states come from the OpenAddresses sources credited there.
  Any new source goes through the same check against the publisher's own terms.

Expected size: about 1,300 more addresses, roughly 5,150 in total. The data file grows from about
660 KB to about 880 KB, and the wheel from 118 KB to about 160 KB.

Known limits, where the floor can be met but the spread cannot without a new source:

- **Indiana** has a public domain source for Bloomington only, and **South Carolina** for Charleston
  only (plus Johns Island).
- **Virginia** needs a public domain source outside Arlington.
- **Connecticut** needs sources for more cities than the two it has.

## Broader geographic coverage

The dataset holds 29 states as of 2.2.0; COVERAGE.md has the current list. Twenty-two are still
unrepresented: DE HI IA KS ME MI MO MS MT ND NE NH NJ NV NY RI SD UT WA WI WV WY.

For 2.2.0 every OpenAddresses source in the thirty-one states missing after 2.1.1 was checked
against the publisher's own terms. Nine states turned up a public domain source, several of them
only on the publisher's portal and not in the copy OpenAddresses points at. The closest misses, each
of which says "no restrictions" or "citation not required" without dedicating the data to the
public domain, and so would need the publisher to confirm in writing:

- **New Jersey** statewide (NJOGIS NG911): free to copy under the state's legal statement, with
  acknowledgement requested, but it includes county-supplied points.
- **Maine** statewide E911: "No restrictions".
- **Wisconsin** statewide parcels: "free for public consumption".
- **Indiana** statewide and **Ohio** statewide (LBRS): permissive, but not a dedication. Both
  states are covered anyway, from Bloomington and Columbus.
- **New York City** AddressPoint and **Seattle**: the cities' open data laws waive restrictions but
  let the city require redistributors to name the source.
- **Iowa** counties, **Detroit** and **Chelan County, WA**: only OpenAddresses calls these public
  domain; the publishers say nothing.

Providence, RI is public domain (PDDL) but was left out: it is 2015 parcel data whose records carry
owner names. New Orleans is CC0 but has no postal codes.

The states that were missing after 2.1.1, for the record: DE HI IA ID IL IN KS LA
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
uncompressed. Since 2.2.0 `_read_features` reads line-delimited and CSV sources a record at a time,
gzipped or not, so the raw text is no longer loaded whole. That is only half the problem: `main()`
still keeps every record that passes validation until it samples, and in a statewide source that is
most of them. A source that size still has to be narrowed before importing.

Bounding that properly means choosing the sample while reading. Reservoir sampling would do it, but
it depends on the order records arrive in, which would undo the guarantee that a seed gives the same
sample whatever the source order. An order-independent alternative is bottom-k sampling: hash each
record's duplicate key together with the seed, and keep the `k` smallest hashes per postal code (for
`--per-postal-code`) and per city (for `--cities`, where `k` is `--count`, since no city's quota can
exceed it). Memory is then bounded by the number of postal codes and cities, not records. The open
question is the Duplicates line of the summary: a repeat of a record that was already evicted can no
longer be recognized as a repeat, so that count would become a lower bound.

## Considered and declined

Ideas that come up, have been weighed, and were turned down on purpose. Recorded so that the
reasoning is not re-derived each time, and so that a change of circumstances that would reopen one
is easy to spot.

### A dataset of a million addresses

Every state and most postal codes could be covered tomorrow by importing Overture Maps or similar
aggregates wholesale. Two things rule that out, in this order:

- **Licensing.** Those aggregates mix licenses record by record, attribution-required and
  share-alike among them, so importing them would end the one promise this library makes: every
  address is public domain. Coverage grows only from sources checked to be public domain;
  `--license` in the ingest script exists to make that check impossible to skip.
- **Weight.** The package is meant to stay light. Even with public domain sources, growth means
  evening out the states and their spread of cities, not piling up volume. That is the 2.3.0 plan
  above.

### Storing the dataset in SQLite

SQLite earns its place at around a million records, where parsing JSON at import is too slow. At a
few thousand, parsing takes milliseconds, and JSON Lines is what makes a data contribution a
reviewable diff; a binary database would make every data pull request unreviewable. Worth revisiting
if the dataset passes about 100,000 records, or if the opt-in performance tests start failing.

### Falling back to looser filters when there are too few matches

That is, answering `real_random_addresses(100, city='X', postal_code='Y')` with addresses from the
same city or the same postal code once the exact matches run out. It returns addresses that do not
satisfy the filters the caller asked for, which is the silent failure 2.0.0 removed by raising
`NoMatchingAddressError`. `count()` answers "how many are there?" up front, and the caller can widen
the filters knowingly.

### Bringing back the 1.x function names

`real_random_address_by_state()` and the rest were replaced in 2.0.0, deliberately, along with
`postalCode` and the empty-dict return. Re-adding them as aliases would mean two spellings of every
call, one of which returns a different key and fails silently. "Upgrading from 1.x" in the README
maps each old name to its replacement.
