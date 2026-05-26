export type GiphyKind = 'gif' | 'sticker'

export type GiphyMediaItem = {
  id: string
  kind: GiphyKind
  title: string
  provider: 'giphy'
  providerId: string
  previewUrl: string
  sendUrl: string
  stillUrl: string
  width: number
  height: number
  animated: boolean
  layoutRatio: number
  tags: string[]
}

type GiphyImage = Record<string, { url?: string; width?: string; height?: string }>

type GiphyObject = {
  id: string
  title?: string
  slug?: string
  url?: string
  images?: GiphyImage
  tags?: string[]
  username?: string
}

const API_BASE = 'https://api.giphy.com/v1'
const DEFAULT_RATING = 'g'
const DEFAULT_LIMIT = 24
const FALLBACK_GIPHY_API_KEY = 'aACmXuwbjQGbcsy942IWA0Ibg55NyqmZ'

function getApiKey() {
  return String(import.meta.env.VITE_GIPHY_API_KEY || FALLBACK_GIPHY_API_KEY || '').trim()
}

function selectUrl(images: GiphyImage | undefined, keys: string[]) {
  if (!images) return ''
  for (const key of keys) {
    const value = images[key]?.url
    if (value) return value
  }
  return ''
}

function selectSize(images: GiphyImage | undefined, keys: string[], dimension: 'width' | 'height') {
  if (!images) return 0
  for (const key of keys) {
    const value = Number(images[key]?.[dimension] || 0)
    if (value) return value
  }
  return 0
}

function normalizeGiphyItem(kind: GiphyKind, item: GiphyObject): GiphyMediaItem {
  const images = item.images || {}
  const previewUrl =
    selectUrl(images, [
      'fixed_width_small_webp',
      'fixed_width_webp',
      'fixed_width_small',
      'fixed_width',
      'preview_webp',
      'downsized_small',
      'original_webp',
      'original',
    ]) || ''

  const stillUrl =
    selectUrl(images, [
      'fixed_width_small_still',
      'fixed_width_still',
      'fixed_width_small',
      'fixed_width',
      'preview',
      'original_still',
    ]) || previewUrl

  const sendUrl =
    kind === 'gif'
      ? selectUrl(images, ['original_mp4', 'original_webp', 'original', 'downsized_medium', 'preview'])
      : selectUrl(images, ['original_webp', 'fixed_height_webp', 'fixed_width_webp', 'original', 'preview'])

  const width = selectSize(images, ['fixed_width_small_webp', 'fixed_width_small', 'fixed_width_webp', 'fixed_width', 'original_webp', 'original'], 'width')
  const height = selectSize(images, ['fixed_width_small_webp', 'fixed_width_small', 'fixed_width_webp', 'fixed_width', 'original_webp', 'original'], 'height')

  return {
    id: item.id,
    kind,
    title: item.title || item.slug || item.id,
    provider: 'giphy',
    providerId: item.id,
    previewUrl,
    sendUrl,
    stillUrl,
    width,
    height,
    animated: kind === 'gif' || Boolean(selectUrl(images, ['original_mp4', 'original_webp'])),
    layoutRatio: width && height ? width / height : 1,
    tags: Array.isArray(item.tags) ? item.tags : [],
  }
}

async function requestGiphy(path: string, params: Record<string, string | number | boolean | undefined>) {
  const apiKey = getApiKey()
  if (!apiKey) {
    throw new Error('Missing GIPHY API key. Set VITE_GIPHY_API_KEY to enable GIFs and stickers.')
  }

  const url = new URL(`${API_BASE}${path}`)
  const requestParams = {
    api_key: apiKey,
    rating: DEFAULT_RATING,
    limit: DEFAULT_LIMIT,
    bundle: 'messaging_non_clips',
    ...params,
  }

  Object.entries(requestParams).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    url.searchParams.set(key, String(value))
  })

  const response = await fetch(url.toString(), {
    headers: {
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`GIPHY request failed with ${response.status}`)
  }

  return response.json()
}

function parseItems(kind: GiphyKind, payload: any): GiphyMediaItem[] {
  const data = Array.isArray(payload?.data) ? payload.data : []
  return data.map((item: GiphyObject) => normalizeGiphyItem(kind, item))
}

export async function fetchGiphyTrending(kind: GiphyKind, offset = 0, limit = DEFAULT_LIMIT) {
  const path = kind === 'gif' ? '/gifs/trending' : '/stickers/trending'
  const payload = await requestGiphy(path, { offset, limit })
  return {
    items: parseItems(kind, payload),
    totalCount: Number(payload?.pagination?.total_count || 0),
    offset: Number(payload?.pagination?.offset || offset),
    count: Number(payload?.pagination?.count || 0),
  }
}

export async function fetchGiphySearch(kind: GiphyKind, query: string, offset = 0, limit = DEFAULT_LIMIT) {
  const path = kind === 'gif' ? '/gifs/search' : '/stickers/search'
  const payload = await requestGiphy(path, { q: query, offset, limit })
  return {
    items: parseItems(kind, payload),
    totalCount: Number(payload?.pagination?.total_count || 0),
    offset: Number(payload?.pagination?.offset || offset),
    count: Number(payload?.pagination?.count || 0),
  }
}

export function getGiphyErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message
  return 'Unable to load GIFs and stickers right now.'
}
