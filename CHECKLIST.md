# Windows + MySQL acceptance checklist

Use a test member and a unique test receipt before entering real data.

- Apply sql/upgrade.sql; confirm existing members and payments still appear.
- Add a member, search by phone, select and edit its name.
- Create a 30-day plan, activate today, check inclusive end date.
- Record a partial payment, refresh and confirm pending balance.
- Repeat exactly the same receipt; verify it does not count twice.
- Repeat the receipt with a different amount; verify rejection.
- Refresh Dashboard and verify total receipts and active-member count.
- Check in twice today; confirm only one attendance row.
- Try attendance for a member without active membership; verify rejection.
- Renew once; confirm next membership starts after the latest end date.
- Load Reports and verify upcoming/active/expired status.
- Export CSV and save a receipt; open the saved files.
- Restart the desktop; confirm data persists.

Do not remove existing database records to install this upgrade.
