# Brave Focus Toggle

A small Windows Python tool that does two jobs through Brave browser policies:

1. **Focus mode** - block distracting sites (whole sites or single sections,
   like `youtube.com/shorts`) and unblock them whenever you choose.
2. **Debloat** - permanently switch off Brave's extras: Rewards, Wallet, VPN,
   News, Talk, Leo AI, and the telemetry pings.

## Requirements

- Windows 10/11 with Brave installed
- Python 3 (no extra packages - standard library only)

## Run it

Double-click `brave-focus.py`, or from a terminal:

```
py brave-focus.py
```

The script asks Windows for admin permission itself, because browser
policies live in a protected part of the registry.

## Menu

```
1. Block sites
2. Unblock sites
3. Show status and list
4. Add a site
5. Remove a site
6. Debloat Brave
0. Exit
```

After any change, restart Brave fully - or open `brave://policy` and click
**Reload policies** - to make Brave notice.

## Your site list

Blocked sites are stored in `focus_sites.txt`, created next to the script
on first run. It starts empty - add sites with menu option 4, or edit the
file by hand (one site per line).

## Notes

- Running any option repeatedly is safe: registry values are overwritten,
  never duplicated, and the blocklist is rebuilt cleanly each time.
- Block/Unblock touches only the `URLBlocklist` policy. Debloat writes
  its own separate policies under
  `HKLM\SOFTWARE\Policies\BraveSoftware\Brave` in the registry.
- Verify everything any time at `brave://policy`.
