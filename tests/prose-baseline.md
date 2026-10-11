# Choosing a storage backend

In this guide we delve into the three backends. It is important to note that the
old backend is still supported. Performance plays a pivotal role in the choice.

The new backend is not just faster, but safer. The change is not a tweak. It is
a rewrite. The rollout was meticulous, and the result is seamless, highlighting
the care of the team.

No new binaries, no new config keys, no new daemons. That is the entire claim.
Consistency is the whole product. The migration did not stop, did not warn, and
did not fail. Experts argue that every rewrite is overdue. Despite these
challenges, the team shipped. Time will tell about the gains.

Turns out the old backend had one table. The backup tool reads both backends.
The restore tool reads both backends. Maybe nobody needed the new one. Maybe it
was faster. Maybe it was safer. Do I use it myself? Do I trust it? The old
backend is dead. That is why the migration mattered. The schema froze; the data
did not.

You already know the answer. The core is small enough to fit in your head, and
it uses sane defaults. Here is the thing: the backup tool reads both backends.
The service sits in the heart of the platform. The release boasts a new
dashboard.
