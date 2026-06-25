# Lucy AI Custom Workspace Rules

## Codebase Backups
Whenever the user requests to create a backup of the project:
1. Locate the next available backup folder index `backup_lucy/backup<N>` (where `<N>` is the incremental number 1, 2, 3, etc. starting at 1).
2. Create that subdirectory.
3. Generate a `.zip` archive of the current committed code using `git archive` (to avoid archiving node_modules, virtual environments, and weights):
   `git archive --format=zip HEAD -o "backup_lucy/backup<N>/Lucy_backup.zip"`
4. Write a `backup_details.txt` file alongside the zip file containing:
   - Date and backup index.
   - Summary of updates and architecture changes.
   - List of tools added, modified, or removed.
   - Delta (what's different) from the previous backup.
