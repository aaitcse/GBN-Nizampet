# GBN Connect

A festival companion app for attendees plus an organiser console, built with Python and Django.
The original single-file HTML prototype kept everything in `localStorage`; this version keeps it
in a real database, so what one phone does (a vote, a photo, a bookmark) is real data the
organisers can see and manage.

## What it does

**Attendee app** (`/`) - a phone-shaped dark UI with five tabs:

| Tab | Behaviour |
| --- | --- |
| Home | Landing screen: hero banner, a visitor counter in the footer, countdown to the festival, dates and venue, live stat tiles, a cross-day "happening soon" carousel, a photo wall, a poll teaser and the practical notes - every card taps through to its tab |
| Events | Day 1..Day N schedule built from the festival dates and opening on today's day, live search over title, stage and category, bookmark any event into "My Bookmarked Agenda" |
| Photos | Approved gallery filtered by Main Stage / Crowd Vibes / Night Lights, tap for a full-screen lightbox, like a photo (once per device), upload your own from the camera roll or by URL |
| Polls | Vote once per poll per device, then see live percentages with your own pick highlighted |
| Feedback | Star rating, category, comment and optional contact - lands in the organiser inbox |

**Organiser console** (`/console/`, staff login required):

- **Overview** - app view counts (total, unique devices, today, a seven day bar chart and which tab people land on); counts for events, photos, polls, votes and feedback; average rating; most-bookmarked events; latest feedback; a quick-approve strip for pending photos.
- **Events** - create, edit, delete, publish/unpublish; per-event bookmark counts; filter by day.
- **Photos** - approve, hide or delete attendee uploads; add official photos.
- **Polls** - publish a poll with 2-4 options, close/reopen it, reset its counters, delete it.
- **Feedback** - filter by status or category, resolve entries, export everything to CSV.

Django's own admin is also wired up at `/django-admin/` for raw data editing.

## Run it

```bash
cd festpulse
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo --admin    # demo content + organiser login
python manage.py runserver
```

- Attendee app: http://127.0.0.1:8000/
- Organiser console: http://127.0.0.1:8000/console/ (`admin` / `festpulse123` from the seeder)
- Django admin: http://127.0.0.1:8000/django-admin/

Use your own account instead of the demo one with `python manage.py createsuperuser`.

Open the attendee app on your phone by running `python manage.py runserver 0.0.0.0:8000` and
visiting `http://<your-computer-ip>:8000/` on the same Wi-Fi (add that IP to
`DJANGO_ALLOWED_HOSTS`).

## Festival dates and the schedule length

The schedule builds its day tabs from `FEST_START_DATE` and `FEST_END_DATE`: a seven day
utsav gets `Day 1 - Mon 14 Sep` through `Day 7 - Sun 20 Sep`, a weekend gets two. Stored
values stay `Day 1`, `Day 2`, ... so existing events survive a date change - only the labels
move, and no migration is needed. While the festival is running the Events tab opens on
today's day instead of Day 1.

## The festival name

The name shown in the app header, the console, the browser tab, the Django admin and the
feedback CSV filename comes from **one place** - `FEST_BRAND` in `config/settings.py`:

```python
FEST_BRAND = os.environ.get("FEST_BRAND", "GBN")
FEST_BRAND_FULL = os.environ.get("FEST_BRAND_FULL", f"{FEST_BRAND} Connect")
FEST_TAGLINE = os.environ.get("FEST_TAGLINE", "Festival Companion")
```

`FEST_BRAND_FULL` is the big gradient title on the app header and login screen (`GBN Connect`);
`FEST_BRAND` is the short form used in page titles and the console footer. Change either value,
or set the matching environment variable, and every page follows - no template edits needed.

## Tests

```bash
python manage.py test
```

46 tests cover the home screen, the attendee flows (search, bookmarks, one-like-per-device, one-vote-per-poll,
upload moderation, feedback validation) and every console action.

## How it is put together

```
config/            settings, root URLs
festival/
  models.py        Event, Bookmark, Photo, PhotoLike, Poll, PollOption, Vote, Feedback, PageView
  views.py         public views + JSON/partial endpoints + console views
  forms.py         event, photo, poll and feedback forms with themed widgets
  urls.py          all routes, namespaced as "festival"
  admin.py         Django admin registration
  context_processors.py   puts the festival name into every template
  tests.py         test suite
  management/commands/seed_demo.py
templates/
  base.html        Tailwind config, fonts, theme
  public/          attendee app shell + partials (home screen, and the lists re-rendered by fetch())
  console/         organiser dashboard pages
static/js/app.js   progressive enhancement layer
static/css/app.css glass-panel theme
```

**Progressive enhancement.** Every attendee action is an ordinary Django `<form>` POST. `app.js`
intercepts those submits, sends them with `fetch()`, and swaps in the server-rendered partial
(`templates/public/partials/`). With JavaScript off, the same forms still work - they just
redirect instead of updating in place. No SPA framework, no build step.

**Who is who.** Attendees are identified by their Django session, so bookmarks, likes and votes
are per-device and need no signup. A unique constraint on `(poll, session_key)` enforces one vote
per poll; `(photo, session_key)` does the same for likes.

**Moderation.** Attendee photo uploads arrive with `is_approved = False` and stay out of the
gallery until an organiser approves them. Set `FEST_AUTO_APPROVE_PHOTOS=1` to publish them
immediately instead.

## Settings worth knowing

Read from the environment (all optional in development):

| Variable | Default | Purpose |
| --- | --- | --- |
| `FEST_BRAND` | `GBN` | Festival name used across the app. |
| `FEST_BRAND_FULL` | `GBN Connect` | Long form for the header and login screen. |
| `FEST_TAGLINE` | `Festival Companion` | Sub-title in the browser tab. |
| `FEST_VENUE` | `GBN Community, Nizampet` | Shown on the home hero. |
| `FEST_EVENT_NAME` | `Ganesh Utsav` | Occasion line above the wordmark on the hero. |
| `FEST_DATES` | `14 - 20 September 2026` | Display dates on the home hero. |
| `FEST_START_DATE` / `FEST_END_DATE` | `2026-09-14` / `2026-09-20` | Drive the countdown badge **and the number of day tabs** (ISO format). |
| `FEST_WELCOME` | short intro | Welcome paragraph under the hero. |
| `FEST_AUTO_APPROVE_PHOTOS` | `0` | Skip photo moderation. |
| `DJANGO_SECRET_KEY` | dev key | **Set this in production.** |
| `DJANGO_DEBUG` | `1` | Set to `0` in production. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | Comma-separated hostnames. |
| `DJANGO_TIME_ZONE` | `Asia/Kolkata` | Timestamps in the console. |

The project folder (`festpulse/`) and the Python packages (`config`, `festival`) are internal
names only - nothing a visitor ever sees. Renaming them is optional and needs the virtualenv
rebuilt afterwards.

## Deploy to Render

The repo is Render-ready: [`render.yaml`](render.yaml) declares the web service and a Postgres
database, [`build.sh`](build.sh) installs dependencies and collects static files, and
[`start.sh`](start.sh) migrates the database, creates the organiser login and starts gunicorn.

Database work belongs in `start.sh`, not `build.sh`: Render's build environment cannot reach the
private database network, so `manage.py migrate` only works once the service is running.

**1. Push this folder to GitHub**

```bash
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

**2. Create the services on Render**

In the Render dashboard: **New > Blueprint**, pick the repo, and Render reads `render.yaml`.
It creates `gbn-festival` (web) and `gbn-db` (Postgres), wires `DATABASE_URL` between them and
generates `DJANGO_SECRET_KEY` for you.

**3. Set the one secret it cannot guess**

`DJANGO_SUPERUSER_PASSWORD` is marked `sync: false`, so Render asks for it at blueprint time (or
set it later under **Environment**). That password, with username `admin`, is your console login.
Set `SEED_DEMO_DATA=1` for the first deploy if you want the demo events, photos and polls loaded.

Deploy finishes at `https://gbn-festival.onrender.com` - attendee app at `/`, console at
`/console/`.

**Doing it without the blueprint:** New > Web Service, connect the repo, then set
Build Command `./build.sh`, Start Command `./start.sh`, and add a Postgres instance **in the same
region** whose `DATABASE_URL` you paste into the service environment.

### Troubleshooting

**Every page returns 500 after a deploy** - the database has no tables yet, which means
`start.sh` did not run. Render stores the start command when the blueprint is *synced*, not on
every deploy, so a service created before `start.sh` existed still runs the old command. Fix it
with Blueprint > **Manual Sync** (or set Start Command to `./start.sh` in the service settings).
`GET /healthz/` tells you which failure it is: `database unreachable` or `migrations not
applied`, and the traceback is in the service log.

**`failed to resolve host 'dpg-...'` / `could not translate host name`** - the web service and the
database are in different regions. `start.sh` runs `wait_for_db` first, which prints this
diagnosis in plain words before the deploy fails. Render's internal database hostnames resolve only within one
region, and a database with no `region:` in the blueprint defaults to `oregon`. A region cannot be
changed after creation, and syncing the blueprint will not move an existing database - so check the
region on both dashboard pages and, if they differ, **delete the database** and re-sync so it is
recreated alongside the service. As a stopgap you can paste the database's **External** URL
(which resolves from anywhere) into the service's `DATABASE_URL`, at the cost of routing traffic
over the public internet.

### What the production settings do

`DJANGO_DEBUG=0` switches on everything a public site needs - and `python manage.py check
--deploy` passes clean:

- **Postgres** through `DATABASE_URL` (`dj-database-url`), falling back to SQLite locally.
- **WhiteNoise** serves hashed, permanently cacheable static files from the web process, so no CDN
  or separate static service is required.
- **HTTPS** - Render terminates TLS and forwards `X-Forwarded-Proto`, so the app redirects to
  HTTPS, marks session and CSRF cookies secure, and sends HSTS.
- **Hosts** - `RENDER_EXTERNAL_HOSTNAME` is added to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
  automatically, so a custom domain only needs `DJANGO_ALLOWED_HOSTS` extended.

### Two things about the free plan

1. **Free instances sleep** after 15 minutes idle; the next visitor waits ~30 seconds for the wake
   up. Fine for testing, not for a festival gate. Upgrade the instance before the event.
2. **Uploaded photo files do not survive a deploy.** Render's disk is ephemeral, so attendee
   uploads (and anything under `media/`) are wiped on each deploy or restart. Photos added by
   *URL* are unaffected - only the stored file bytes are lost. Two fixes:
   - Attach a Render **persistent disk** (paid instance), mount it at e.g. `/var/data/media`, and
     set `DJANGO_MEDIA_ROOT=/var/data/media`. The app reads that variable already.
   - Or move media to object storage (S3/Cloudinary) with `django-storages`.

### Free Postgres expires

Render's free Postgres is deleted 30 days after creation. For a real event use a paid database
plan, or export and reload with `pg_dump` / `pg_restore` before it lapses.
