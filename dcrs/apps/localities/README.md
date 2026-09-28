# apps/localities/

Provides the four-level geographic hierarchy used across DCRS to locate citizens, issues, and officer assignments. The structure mirrors Tanzania's official administrative boundaries.

## Hierarchy

```
Region
  └── District (many per Region)
        └── Ward  (many per District)
              └── Mtaa  (many per Ward — street/neighbourhood)
```

## Models

### `Region`
Top-level administrative area (e.g. Dar es Salaam, Mwanza, Dodoma).

| Field | Type |
|---|---|
| `name` | CharField (unique) |

### `District`
Sub-division of a Region (e.g. Kinondoni, Ilala, Temeke).

| Field | Type |
|---|---|
| `name` | CharField |
| `region` | ForeignKey → Region |

Unique together: `(region, name)`

### `Ward`
Sub-division of a District (e.g. Mwananyamala, Sinza, Kariakoo).

| Field | Type |
|---|---|
| `name` | CharField |
| `district` | ForeignKey → District |

Unique together: `(district, name)`

### `Mtaa`
Smallest unit — a street or neighbourhood within a Ward (e.g. Sinza Palestina, Kariakoo Kati).

| Field | Type |
|---|---|
| `name` | CharField |
| `ward` | ForeignKey → Ward |

Unique together: `(ward, name)`

## API

The localities app exposes a JSON API used by the registration form for cascading dropdowns (District → Ward → Mtaa updates when Region changes).

Base URL: `/api/localities/`

Check `urls.py` and `views.py` for the specific endpoints.

## Seeded data

The `seed` command populates:
- 3 Regions: Dar es Salaam, Mwanza, Dodoma
- 5 Districts: Kinondoni, Ilala, Temeke, Nyamagana, Dodoma Urban
- 6 Wards: Mwananyamala, Sinza, Kariakoo, Mbagala, Isamilo, Dodoma Central
- 5 Mitaa: one per ward (Mwananyamala Mashariki, Sinza Palestina, Kariakoo Kati, Mbagala Rangi Tatu, Isamilo Juu)
