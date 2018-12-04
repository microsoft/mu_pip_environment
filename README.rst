
==============
MU Environment
==============

About
=====

Entry point into Self Describing Environment (SDE). Sets up and parses state of workspace before calling into build.
Please see Project Mu for details https://microsoft.github.io/mu

Version History
===============

0.2.5
----

Moved tests and added CI and local build documentation
Added VersionAggregator to collect global version information

0.2.4
-----

Fixing repo resolver cloning logic

0.2.3
-----

Fixing self.RunCmd reference in UefiBuild

0.2.2
-----

Fixing edge case in RepoResolver, removing self.RunCmd from UefiBuilder

0.2.1
-----

Fixing error in UefiBuild where spaces weren't placed between parameters

0.2.0
-----

Initial commit