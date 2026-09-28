"""Shared constants for the One-Stop Emergency & Services Centre.

Lives here (rather than inline in the view) so the Django template view and the API
(``GET /api/v1/issues/services/``) read from one source and cannot drift apart.
"""

SERVICE_TILES = [
    {
        "category": "WATER",
        "label": "Water",
        "icon": "bi-droplet",
        "desc": "Pipe bursts, no supply, reconnection",
    },
    {
        "category": "ELECTRICITY",
        "label": "Electricity",
        "icon": "bi-lightning-charge",
        "desc": "Outages, new connections, faults",
    },
    {
        "category": "SANITATION",
        "label": "Waste",
        "icon": "bi-trash",
        "desc": "Uncollected garbage, pickup scheduling",
    },
    {
        "category": "ROAD",
        "label": "Roads",
        "icon": "bi-signpost-split",
        "desc": "Potholes, flooding, road repairs",
    },
    {
        "category": "SECURITY",
        "label": "Security",
        "icon": "bi-shield-exclamation",
        "desc": "Crime, suspicious activity, patrols",
    },
]