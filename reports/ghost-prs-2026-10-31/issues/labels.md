## Issue Summary

Bulk removal of several labels can finish only partly while reporting success. The Admin sends one request per label with the same member filter. If the first removal changes that filter's matches, later requests no longer select those members.

Suggested priority: **P2**. The demonstrated case is a normal bulk operation filtered by a label that is among those being removed.

## Steps to Reproduce

1. Create a member with labels **Alpha** (slug `alpha`) and **Zeta** (slug `zeta`).
2. Filter Members by Alpha and apply the bulk action to all matching members.
3. Choose Remove labels, select Alpha first and Zeta second, then confirm. Check that Alpha is the first label submitted; the outcome depends on this order.
4. Reopen the member after the success notification.

**Expected:** both selected labels are removed from the original selection.

**Actual:** Alpha is removed, Zeta remains, and the handler reports `Labels removed successfully`. The two operations return `successful: 1` then `successful: 0`.

Controls: use an independent email filter, or remove Zeta before Alpha. Both labels are then removed.

## Cause

[MembersActions sends sequential requests](https://github.com/TryGhost/Ghost/blob/5d4430c8c157990adbd69400f4cee9795037fbbb/apps/admin/src/members/components/members-actions.tsx#L110) and [the repository re-evaluates the filter for each request](https://github.com/TryGhost/Ghost/blob/5d4430c8c157990adbd69400f4cee9795037fbbb/ghost/core/server/services/members/members-api/repositories/member-repository.js#L1229). After Alpha is removed, the same `label:[alpha]` filter selects no members.

## Validation

Reproduced on source commit `5d4430c8c157990adbd69400f4cee9795037fbbb` with Node 22.23.4, React/jsdom, the actual modal/handler, mutation configuration, member repository/model/filter plugins, and real SQLite queries in memory. A diagnostic asserted the partial result plus both controls and exited **0**. The assertion requiring an empty remaining-label list failed as expected.

HTTP transport, visual components and the label picker were adapted. The actual filtering and relation removal were not simulated. The test supplied the supported filter directly; it did not execute the full filter-building screen or a real browser. The adapted picker's fixed option order does not establish order independence from clicks in the real picker.

The endpoint's HTTP-200 behavior was checked by reading its source, not by executing HTTP. No MySQL or full-server test is claimed for this reproduction.

Related work checked: #28510 concerns mutation errors in label creation/editing, and #24734 concerns creating a label during bulk addition; neither addresses reusing a filter changed by the first removal.

## Ghost Version

Source `6.74.0-rc.0`, commit `5d4430c8c157990adbd69400f4cee9795037fbbb`.

## Node.js Version

22.23.4.

## How did you install Ghost?

Isolated source-module reproduction on Windows with existing dependencies and a disposable in-memory database.

## Database type

SQLite3 for the reproduction.

## Browser & OS version

Windows; jsdom, not a real-browser E2E run.

## Code of Conduct

- [x] I agree to be friendly and polite to people in this repository.

