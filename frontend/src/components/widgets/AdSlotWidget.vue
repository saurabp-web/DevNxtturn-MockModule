<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { InformationCircleIcon } from '@heroicons/vue/24/outline'

// --- ENVIRONMENT DETECTION ---
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
const isDevCloud = window.location.hostname === 'dev.nxtturn.com'

// --- THE TOGGLE ---
// We show REAL ads only if it's NOT local and NOT the dev site.
// This means once you point "www.nxtturn.com" here, ads turn on automatically!
const shouldShowRealAds = !isLocal && !isDevCloud

const isLoading = ref(true)
const currentAd = ref<any>(null)

// Mock Ads (Your fallback)
const mockAds = [
  {
    provider: 'Skillshare',
    title: 'Start Your Free Trial',
    image: 'https://picsum.photos/seed/skill/300/150',
    url: 'https://skillshare.com',
  },
  {
    provider: 'Coursera',
    title: 'Get a Degree',
    image: 'https://picsum.photos/seed/edu/300/150',
    url: 'https://coursera.org',
  },
]

const handleAdClick = () => {
  if (currentAd.value && currentAd.value.url) {
    window.open(currentAd.value.url, '_blank')
  }
}

onMounted(() => {
  if (shouldShowRealAds) {
    // 1. PRODUCTION LOGIC: Initialize Real AdSense
    nextTick(() => {
      setTimeout(() => {
        try {
          const adsbygoogle = (window as any).adsbygoogle || []
          adsbygoogle.push({})
          isLoading.value = false
        } catch (e) {
          console.error('AdSense error', e)
          isLoading.value = false
        }
      }, 1000)
    })
  } else {
    // 2. DEV/LOCAL LOGIC: Show Mock Ad
    setTimeout(() => {
      currentAd.value = mockAds[Math.floor(Math.random() * mockAds.length)]
      isLoading.value = false
    }, 800)
  }
})
</script>

<template>
  <div class="bg-gray-50 p-4 rounded-2xl border border-gray-100 flex flex-col min-h-[180px]">
    <div class="flex items-center justify-between mb-3">
      <span class="text-[9px] font-black text-gray-400 uppercase tracking-widest">
        {{ shouldShowRealAds ? 'Advertisement' : 'Sponsor Spotlight' }}
      </span>
      <InformationCircleIcon class="w-3 h-3 text-gray-300 cursor-help" />
    </div>

    <!-- LOADING STATE -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="w-full h-24 bg-gray-200 rounded-xl animate-pulse"></div>
    </div>

    <!-- OPTION A: REAL ADS (Active on Production Domain) -->
    <template v-if="shouldShowRealAds">
      <ins
        class="adsbygoogle"
        style="display: block"
        data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
        data-ad-slot="XXXXXXXXXX"
        data-ad-format="auto"
        data-full-width-responsive="true"
      ></ins>
    </template>

    <!-- OPTION B: MOCK ADS (Active on Localhost and dev.nxtturn.com) -->
    <div
      v-else-if="currentAd"
      class="flex-1 flex flex-col group cursor-pointer"
      @click="handleAdClick"
    >
      <div class="relative overflow-hidden rounded-xl mb-3 h-24">
        <img
          :src="currentAd.image"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform"
        />
      </div>
      <h4 class="text-xs font-bold text-gray-800 mb-1">{{ currentAd.title }}</h4>
      <div class="flex items-center justify-between mt-auto pt-2 border-t border-gray-200/50">
        <span class="text-[10px] font-bold text-blue-600">{{ currentAd.provider }}</span>
        <span class="text-[10px] text-gray-400">Visit Site</span>
      </div>
    </div>
  </div>
</template>
