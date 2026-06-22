# GitHub App Access to `.github-private`

Coding agents need access to NeuroLift governance files before they start work.
If the GitHub App that powers an agent is installed for **Selected
repositories**, it may be able to read the working repo but not
`NeuroLift-Technologies/.github-private`.

## Symptoms

- Private governance links in `AGENTS.md` return `404`.
- `NLT-DEV-OTOI.md` or `.github-private` cannot be fetched by an agent.
- Agents fall back to the public governance mirrors even though private access
  should be available.

## Fix

Only a NeuroLift organization admin or someone with permission to configure the
GitHub App installation can change this access.

1. Open the organization installation settings:
   `https://github.com/organizations/NeuroLift-Technologies/settings/installations`
2. Find the app used by the agent workflow, such as Cursor, Copilot, Codex, or
   another coding-agent integration.
3. Select **Configure**.
4. Under **Repository access**, choose either:
   - **All repositories**, or
   - **Selected repositories** with both the working repository and
     `.github-private` selected.
5. Save the installation settings.
6. Re-run the agent session-start check.

## Safe fallback

If private access cannot be granted immediately, agents may read the public
mirrors referenced in `AGENTS.md`:

- `https://github.com/NeuroLift-Technologies/.github/blob/main/governance/NLT-DEV-OTOI.md`
- `https://github.com/NeuroLift-Technologies/.github/blob/main/governance/AGENTS.md`

Record the access limitation in the session registration or handoff so the next
agent knows whether private governance access was available.

## What not to do

- Do not copy secrets, credentials, or private repository content into a public
  issue or pull request.
- Do not proceed with architectural, deployment, external-integration, or
  safety-critical decisions when the required governance source is unavailable.
- Do not modify `NLT-DEV-OTOI.md`; governance amendments require Joshua W.
  Dorsey, Sr.'s explicit approval and the formal OTOI amendment process.
