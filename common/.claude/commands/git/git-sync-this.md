Commit and push only changes made in this session across all project repos (working directory + additional working directories) but only for the most recent branch we worked on (excluding bead branch).

- Group changes by feature/fix/purpose
- Ignore unrelated pre-existing changes
- Run `bd sync` before and after commits if beads exists
- Push all changes to remote
