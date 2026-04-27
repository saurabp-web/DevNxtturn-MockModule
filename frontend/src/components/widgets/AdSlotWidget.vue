<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { InformationCircleIcon } from '@heroicons/vue/24/outline'

// --- DYNAMIC MODE DETECTION (Cloud-Ready) ---
// We only show real Google Ads if the environment variable is explicitly set to 'production'
const shouldShowRealAds = import.meta.env.VITE_AD_MODE === 'production'

const isLoading = ref(true)
const currentAd = ref<any>(null)

// --- MOCK AD LIBRARY (50+ Entries) ---
const mockAds = [
  {
    provider: 'Skillshare',
    title: 'Master Creative Skills',
    image: 'https://picsum.photos/seed/skill/300/150',
    url: 'https://skillshare.com',
  },
  {
    provider: 'Coursera',
    title: 'Earn a University Degree',
    image: 'https://picsum.photos/seed/edu/300/150',
    url: 'https://coursera.org',
  },
  {
    provider: 'Udemy',
    title: '100,000+ Online Courses',
    image: 'https://picsum.photos/seed/code/300/150',
    url: 'https://udemy.com',
  },
  {
    provider: 'DigitalOcean',
    title: 'Spin up a Droplet in Seconds',
    image: 'https://picsum.photos/seed/cloud/300/150',
    url: 'https://digitalocean.com',
  },
  {
    provider: 'Vercel',
    title: 'Deploy Your Frontend Instantly',
    image: 'https://picsum.photos/seed/deploy/300/150',
    url: 'https://vercel.com',
  },
  {
    provider: 'GitHub',
    title: 'Where the World Builds Software',
    image: 'https://picsum.photos/seed/git/300/150',
    url: 'https://github.com',
  },
  {
    provider: 'Notion',
    title: 'Your Connected Workspace',
    image: 'https://picsum.photos/seed/note/300/150',
    url: 'https://notion.so',
  },
  {
    provider: 'Slack',
    title: 'Make Work Life Simpler',
    image: 'https://picsum.photos/seed/slack/300/150',
    url: 'https://slack.com',
  },
  {
    provider: 'Figma',
    title: 'Design Together, Faster',
    image: 'https://picsum.photos/seed/design/300/150',
    url: 'https://figma.com',
  },
  {
    provider: 'Canva',
    title: 'Design Anything in Minutes',
    image: 'https://picsum.photos/seed/canva/300/150',
    url: 'https://canva.com',
  },
  {
    provider: 'AWS',
    title: 'Build on the Cloud Leader',
    image: 'https://picsum.photos/seed/aws/300/150',
    url: 'https://aws.amazon.com',
  },
  {
    provider: 'Google Cloud',
    title: 'AI-First Infrastructure',
    image: 'https://picsum.photos/seed/gcp/300/150',
    url: 'https://cloud.google.com',
  },
  {
    provider: 'MongoDB',
    title: 'The Developer Data Platform',
    image: 'https://picsum.photos/seed/mongo/300/150',
    url: 'https://mongodb.com',
  },
  {
    provider: 'Postman',
    title: 'API Development Platform',
    image: 'https://picsum.photos/seed/api/300/150',
    url: 'https://postman.com',
  },
  {
    provider: 'Datadog',
    title: 'Modern Monitoring & Analytics',
    image: 'https://picsum.photos/seed/data/300/150',
    url: 'https://datadoghq.com',
  },
  {
    provider: 'Sentry',
    title: 'Stop Guessing, Start Fixing',
    image: 'https://picsum.photos/seed/error/300/150',
    url: 'https://sentry.io',
  },
  {
    provider: 'Linear',
    title: 'The Better Way to Build Product',
    image: 'https://picsum.photos/seed/product/300/150',
    url: 'https://linear.app',
  },
  {
    provider: 'Loom',
    title: 'Video Messages for Work',
    image: 'https://picsum.photos/seed/video/300/150',
    url: 'https://loom.com',
  },
  {
    provider: 'Grammarly',
    title: 'Write with Confidence',
    image: 'https://picsum.photos/seed/write/300/150',
    url: 'https://grammarly.com',
  },
  {
    provider: 'Webflow',
    title: 'Build Professional Websites',
    image: 'https://picsum.photos/seed/web/300/150',
    url: 'https://webflow.com',
  },
  {
    provider: 'Stripe',
    title: 'Payments for the Internet',
    image: 'https://picsum.photos/seed/pay/300/150',
    url: 'https://stripe.com',
  },
  {
    provider: 'Shopify',
    title: 'Start Your Business Today',
    image: 'https://picsum.photos/seed/shop/300/150',
    url: 'https://shopify.com',
  },
  {
    provider: 'Spotify',
    title: 'Focus Music for Coders',
    image: 'https://picsum.photos/seed/music/300/150',
    url: 'https://spotify.com',
  },
  {
    provider: 'Asana',
    title: 'Manage Team Projects Online',
    image: 'https://picsum.photos/seed/task/300/150',
    url: 'https://asana.com',
  },
  {
    provider: 'Trello',
    title: 'Collaborate and Get More Done',
    image: 'https://picsum.photos/seed/card/300/150',
    url: 'https://trello.com',
  },
  {
    provider: 'Airtable',
    title: 'Connect Everything, Achieve Anything',
    image: 'https://picsum.photos/seed/base/300/150',
    url: 'https://airtable.com',
  },
  {
    provider: 'Discord',
    title: 'Join Your Dev Community',
    image: 'https://picsum.photos/seed/chat/300/150',
    url: 'https://discord.com',
  },
  {
    provider: 'Zoom',
    title: 'One Platform to Connect',
    image: 'https://picsum.photos/seed/meet/300/150',
    url: 'https://zoom.us',
  },
  {
    provider: 'Microsoft Azure',
    title: 'Innovate with Purpose',
    image: 'https://picsum.photos/seed/azure/300/150',
    url: 'https://azure.microsoft.com',
  },
  {
    provider: 'Heroku',
    title: 'Build, Run, Scale Apps',
    image: 'https://picsum.photos/seed/hoku/300/150',
    url: 'https://heroku.com',
  },
  {
    provider: 'Netlify',
    title: 'Better Web, Faster',
    image: 'https://picsum.photos/seed/ntly/300/150',
    url: 'https://netlify.com',
  },
  {
    provider: 'BrowserStack',
    title: 'App & Browser Testing',
    image: 'https://picsum.photos/seed/test/300/150',
    url: 'https://browserstack.com',
  },
  {
    provider: 'Twilio',
    title: 'Engage Your Customers Everywhere',
    image: 'https://picsum.photos/seed/sms/300/150',
    url: 'https://twilio.com',
  },
  {
    provider: 'Mailchimp',
    title: 'Turn Emails into Revenue',
    image: 'https://picsum.photos/seed/mail/300/150',
    url: 'https://mailchimp.com',
  },
  {
    provider: 'Intercom',
    title: 'The Only AI Customer Service Platform',
    image: 'https://picsum.photos/seed/talk/300/150',
    url: 'https://intercom.com',
  },
  {
    provider: 'HubSpot',
    title: 'Grow Better with CRM',
    image: 'https://picsum.photos/seed/crm/300/150',
    url: 'https://hubspot.com',
  },
  {
    provider: 'Zapier',
    title: 'Automate Your Busy Work',
    image: 'https://picsum.photos/seed/auto/300/150',
    url: 'https://zapier.com',
  },
  {
    provider: 'LastPass',
    title: 'Secure Your Passwords',
    image: 'https://picsum.photos/seed/lock/300/150',
    url: 'https://lastpass.com',
  },
  {
    provider: '1Password',
    title: 'Go Ahead, Forget Your Passwords',
    image: 'https://picsum.photos/seed/key/300/150',
    url: 'https://1password.com',
  },
  {
    provider: 'NordVPN',
    title: 'Stay Safe Online',
    image: 'https://picsum.photos/seed/vpn/300/150',
    url: 'https://nordvpn.com',
  },
  {
    provider: 'Codecademy',
    title: 'Learn to Code for Free',
    image: 'https://picsum.photos/seed/learn/300/150',
    url: 'https://codecademy.com',
  },
  {
    provider: 'Pluralsight',
    title: 'Build Tech Skills in Teams',
    image: 'https://picsum.photos/seed/sight/300/150',
    url: 'https://pluralsight.com',
  },
  {
    provider: 'Brilliant',
    title: 'Learn Math, Science, and CS',
    image: 'https://picsum.photos/seed/math/300/150',
    url: 'https://brilliant.org',
  },
  {
    provider: 'MasterClass',
    title: 'Learn from the Best',
    image: 'https://picsum.photos/seed/star/300/150',
    url: 'https://masterclass.com',
  },
  {
    provider: 'Adobe CC',
    title: 'Creativity for All',
    image: 'https://picsum.photos/seed/adobe/300/150',
    url: 'https://adobe.com',
  },
  {
    provider: 'Sketch',
    title: 'The Designer’s Tool',
    image: 'https://picsum.photos/seed/sketch/300/150',
    url: 'https://sketch.com',
  },
  {
    provider: 'InVision',
    title: 'Collaborative Design',
    image: 'https://picsum.photos/seed/vision/300/150',
    url: 'https://invisionapp.com',
  },
  {
    provider: 'Behance',
    title: 'Showcase Your Portfolio',
    image: 'https://picsum.photos/seed/port/300/150',
    url: 'https://behance.net',
  },
  {
    provider: 'Dribbble',
    title: 'Design Inspiration',
    image: 'https://picsum.photos/seed/drib/300/150',
    url: 'https://dribbble.com',
  },
  {
    provider: 'Medium',
    title: 'Human Stories and Ideas',
    image: 'https://picsum.photos/seed/blog/300/150',
    url: 'https://medium.com',
  },
  {
    provider: 'Substack',
    title: 'Independent Publishing',
    image: 'https://picsum.photos/seed/news/300/150',
    url: 'https://substack.com',
  },
  {
    provider: 'NxtTurn',
    title: 'Build Your Tech Future',
    image: 'https://picsum.photos/seed/nxt/300/150',
    url: 'https://nxtturn.com',
  },
]

const handleAdClick = () => {
  if (currentAd.value && currentAd.value.url) {
    window.open(currentAd.value.url, '_blank')
  }
}

onMounted(() => {
  if (shouldShowRealAds) {
    // 1. PRODUCTION LOGIC: Real AdSense
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
    // 2. MOCK LOGIC: Pick a fresh ad and force the image to refresh
    setTimeout(() => {
      const selected = mockAds[Math.floor(Math.random() * mockAds.length)]

      // We add '?t=' with a timestamp to the image URL.
      // This "tricks" the browser into showing a brand-new image every time.
      currentAd.value = {
        ...selected,
        image: `${selected.image}?t=${Date.now()}`,
      }

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
      <InformationCircleIcon
        class="w-3 h-3 text-gray-300 cursor-help"
        title="Mock ads shown in development mode"
      />
    </div>

    <!-- LOADING STATE -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="w-full h-24 bg-gray-200 rounded-xl animate-pulse"></div>
    </div>

    <!-- OPTION A: REAL ADS (Active only when VITE_AD_MODE is 'production') -->
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

    <!-- OPTION B: MOCK ADS (Active in Local/Dev/Nip.io) -->
    <div
      v-else-if="currentAd"
      class="flex-1 flex flex-col group cursor-pointer"
      @click="handleAdClick"
    >
      <div class="relative overflow-hidden rounded-xl mb-3 h-24">
        <img
          :src="currentAd.image"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          :alt="currentAd.provider"
        />
        <div class="absolute inset-0 bg-black/5 group-hover:bg-transparent transition-colors"></div>
      </div>

      <h4
        class="text-[13px] font-bold text-gray-800 mb-1 leading-tight group-hover:text-blue-600 transition-colors"
      >
        {{ currentAd.title }}
      </h4>

      <div class="flex items-center justify-between mt-auto pt-2 border-t border-gray-200/50">
        <span class="text-[10px] font-bold text-blue-600 uppercase tracking-tight">{{
          currentAd.provider
        }}</span>
        <span class="text-[10px] text-gray-400 font-medium group-hover:text-gray-600"
          >Learn More &rarr;</span
        >
      </div>
    </div>
  </div>
</template>
