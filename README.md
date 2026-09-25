<h1 align="center">Colin de Vries</h1>

<p align="center">
  Software engineer in Groningen, Netherlands.<br>
  I reverse engineer devices, publish the client, and ship the Home Assistant integration.
</p>

<p align="center">
  <a href="https://cdevries.dev"><img alt="Website" src="https://img.shields.io/badge/cdevries.dev-1f2328?style=flat-square&logo=firefoxbrowser&logoColor=white"></a>
  <a href="mailto:colin@cdevries.dev"><img alt="Email" src="https://img.shields.io/badge/colin%40cdevries.dev-2a78d6?style=flat-square&logo=maildotru&logoColor=white"></a>
  <a href="https://github.com/AboveColin?tab=repositories"><img alt="Repositories" src="https://img.shields.io/badge/33%20own%20repos-0d1117?style=flat-square&logo=github&logoColor=white"></a>
  <a href="https://hacs.xyz"><img alt="HACS" src="https://img.shields.io/badge/3%20in%20HACS-41bdf5?style=flat-square&logo=homeassistant&logoColor=white"></a>
</p>

Most of what I publish follows one shape. I find a device or a service whose API
nobody wrote down, work the protocol out of the app that talks to it, publish a
clean async Python client, then build a Home Assistant integration on top of that
client. The client stays useful on its own, so the next person does not have to
repeat the hard part. Three integrations are in the HACS default store and three
more are in review.

The rest of my time goes into the platform that runs all of it at home: a Proxmox
cluster and NixOS hosts, the whole configuration in one flake, deployed by a script
that shows dry activation, runs the tests, switches, and then checks that the host
reports the revision it was given.

<!-- stars:start -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/AboveColin/AboveColin/main/assets/stars-dark.svg?v=4c3100d3">
    <img alt="Cumulative GitHub stars over time: 126 stars across 28 repositories" src="https://raw.githubusercontent.com/AboveColin/AboveColin/main/assets/stars-light.svg?v=4c3100d3" width="880">
  </picture>
</p>

<p align="center">
  <strong>126</strong> stars &middot; <strong>35</strong> own public repositories &middot; <strong>28</strong> of them starred by someone &middot; last star 2026-09-25
</p>

### Most starred

| Project | What it does | Stars |
| --- | --- | --: |
| [HA-Jev](https://github.com/AboveColin/HA-Jev) | Ask your house a question, get a number back. Home Assistant integration for TypeSafe Jev: ty... | 63 |
| [HA-Philips-Pet-Series](https://github.com/AboveColin/HA-Philips-Pet-Series) | Home Assistant integration for Philips Pet Series smart pet feeders. Feed from a dashboard, u... | 14 |
| [HA-Forgejo](https://github.com/AboveColin/HA-Forgejo) | Home Assistant integration for Forgejo | 5 |
| [petsseries](https://github.com/AboveColin/petsseries) | Unofficial async Python client for the Philips Pet Series (Versuni) API: homes, devices, meal... | 4 |
| [remote-for-xirp](https://github.com/AboveColin/remote-for-xirp) | Remote For Xirp — mobile web control surface for the Xirp agent daemon: machines, projects, s... | 4 |
| [HA-Fitdays](https://github.com/AboveColin/HA-Fitdays) | Home Assistant integration for Fitdays / ICOMON smart scales (Robi S6) — full body compositio... | 3 |
| [jevclient](https://github.com/AboveColin/jevclient) | Async Python client for TypeSafe Jev. Typed questions in, probabilities and choices out, no p... | 3 |
| [HA-Basic-Fit](https://github.com/AboveColin/HA-Basic-Fit) | Home Assistant integration for Basic-Fit (HACS) — visits, membership, body measurements and b... | 2 |
| [HA-Traefik](https://github.com/AboveColin/HA-Traefik) | Home Assistant integration for Traefik: a device per route, named after the hostname it serves | 2 |
| [fitdays](https://github.com/AboveColin/fitdays) | Unofficial async Python client for the Fitdays (ICOMON) smart-scale cloud API — Robi S6 and r... | 2 |
<!-- stars:end -->

### Device to dashboard

Each row is the same pattern twice: a standalone API client, and the integration
that uses it.

| Device or service | Python client | Home Assistant integration | Availability |
| --- | --- | --- | --- |
| Philips Pet Series feeders and cameras | [petsseries](https://github.com/AboveColin/petsseries) | [HA-Philips-Pet-Series](https://github.com/AboveColin/HA-Philips-Pet-Series) | HACS default |
| Traefik | [traefik](https://github.com/AboveColin/traefik) | [HA-Traefik](https://github.com/AboveColin/HA-Traefik) | HACS default |
| Forgejo | [forgejo](https://github.com/AboveColin/forgejo) | [HA-Forgejo](https://github.com/AboveColin/HA-Forgejo) | HACS default |
| Fitdays / ICOMON smart scales | [fitdays](https://github.com/AboveColin/fitdays) | [HA-Fitdays](https://github.com/AboveColin/HA-Fitdays) | HACS review |
| Basic-Fit | [basicfit](https://github.com/AboveColin/basicfit) | [HA-Basic-Fit](https://github.com/AboveColin/HA-Basic-Fit) | HACS review |
| Ziggo and other Liberty Global gateways | [liberty-global-gateway](https://github.com/AboveColin/liberty-global-gateway) | [HA-Liberty-Global-Gateway](https://github.com/AboveColin/HA-Liberty-Global-Gateway) | HACS review |
| ENGIE Netherlands | [engie-nl](https://github.com/AboveColin/engie-nl) | [HA-ENGIE-NL](https://github.com/AboveColin/HA-ENGIE-NL) | custom repository |
| Stremio | [stremio-py](https://github.com/AboveColin/stremio-py) | [stremio-ha](https://github.com/AboveColin/stremio-ha) | custom repository |

### Other work

- [tuya-mobile](https://github.com/AboveColin/tuya-mobile) reimplements the Tuya
  mobile app security layer in pure Python, so a camera answers to my own code
  instead of the vendor app.
- [switchMCP](https://github.com/AboveColin/switchMCP) puts a homebrew Nintendo
  Switch behind MCP, which lets an agent manage it over the network.
- [remote-for-xirp](https://github.com/AboveColin/remote-for-xirp) is a mobile web
  control surface for a coding agent daemon.
- [hevy-api-knowledge](https://github.com/AboveColin/hevy-api-knowledge) documents
  the Hevy workout API, both the public v1 and the one the app actually uses.

<p align="center">
  <a href="https://cdevries.dev">cdevries.dev</a> &middot;
  <a href="mailto:colin@cdevries.dev">colin@cdevries.dev</a> &middot;
  <a href="https://x.com/AboveColin">@AboveColin</a>
</p>
