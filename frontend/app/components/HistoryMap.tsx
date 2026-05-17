'use client'

import { ComposableMap, Geographies, Geography } from 'react-simple-maps'

import type { MapData } from '../lib/types'

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

const COLOR_MAP: Record<string, string> = {
  red: '#ef4444',
  blue: '#3b82f6',
  green: '#22c55e',
  yellow: '#eab308',
  purple: '#a855f7',
  orange: '#f97316',
}

const COUNTRY_ALIASES: Record<string, string> = {
  'united states': 'united states of america',
  'usa': 'united states of america',
  'us': 'united states of america',
  'america': 'united states of america',
  'uk': 'united kingdom',
  'great britain': 'united kingdom',
  'britain': 'united kingdom',
  'england': 'united kingdom',
  'türkiye': 'turkey',
  'czechia': 'czech republic',
  'south korea': 'korea, republic of',
  'north korea': "korea, dem. people's rep. of",
  'russia': 'russia',
  'soviet union': 'russia',
  'ussr': 'russia',
  'bosnia and herzegovina': 'bosnia and herz.',
  'congo': 'dem. rep. congo',
  'democratic republic of the congo': 'dem. rep. congo',
  'ivory coast': "côte d'ivoire",
  'cote d ivoire': "côte d'ivoire",
  'east timor': 'timor-leste',
  'myanmar': 'myanmar',
  'burma': 'myanmar',
  'dominican republic': 'dominican rep.',
  'central african republic': 'central african rep.',
  'south sudan': 's. sudan',
  'equatorial guinea': 'eq. guinea',
  'falkland islands': 'falkland is.',
  'solomon islands': 'solomon is.',
}

function normalizeName(name: string): string {
  return COUNTRY_ALIASES[name.trim().toLowerCase()] ?? name.trim().toLowerCase()
}

interface Props {
  mapData: MapData
}

export default function HistoryMap({ mapData }: Props) {
  const countryColorMap: Record<string, string> = {}

  mapData.factions.forEach((faction) => {
    const color = COLOR_MAP[faction.color] || '#52525b'
    faction.countries.forEach((country) => {
      countryColorMap[normalizeName(country)] = color
    })
  })

  const getColor = (geoName: string) => {
    return countryColorMap[normalizeName(geoName)] || '#27272a'
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl overflow-hidden border border-zinc-900 bg-zinc-950 max-h-[min(50vh,340px)] sm:max-h-none overflow-x-auto">
        <ComposableMap
          projectionConfig={{ scale: 120 }}
          style={{ width: '100%', height: 'auto', minWidth: 280 }}
        >
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={getColor(geo.properties.name)}
                  stroke="#18181b"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: 'none' },
                    hover: { outline: 'none', opacity: 0.8 },
                    pressed: { outline: 'none' },
                  }}
                />
              ))
            }
          </Geographies>
        </ComposableMap>
      </div>

      <div className="flex flex-wrap gap-3">
        {mapData.factions.map((faction) => (
          <div key={faction.name} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full shrink-0"
              style={{ backgroundColor: COLOR_MAP[faction.color] || '#52525b' }}
            />
            <span className="text-zinc-400 text-xs">{faction.name}</span>
          </div>
        ))}
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-zinc-800 shrink-0" />
          <span className="text-zinc-600 text-xs">Neutral / Unaffected</span>
        </div>
      </div>

      {mapData.year && (
        <p className="text-zinc-600 text-xs">Approximate year: {mapData.year}</p>
      )}
    </div>
  )
}
