# Security

Report security issues using the repository's private vulnerability reporting form:
https://github.com/ozkurt23/humanoid_eureka_exp/security/advisories/new

Keep credentials and exploit details in that private report. Include the affected revision, reproduction steps and expected impact. Research failures and motion-quality issues can be reported in ordinary issues.

The maintained reproduction entry point is the current main branch. Historical releases preserve experiments and their original dependency versions. Dependency updates should be checked against the recorded simulation because numerical changes can affect results.

The project runs local simulation, archive extraction and rendering tools. Use an isolated Python environment as documented. The archive restore tool verifies SHA-256 records and creates files in a new or empty destination. Read scripts before running them, especially changes contributed by others.

The public project allows viewing, downloading and forking. Repository write access is managed separately by its owner. Reported security findings are investigated as a best-effort research-project maintenance task.
