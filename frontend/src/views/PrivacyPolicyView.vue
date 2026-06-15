<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<template>
  <div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 md:p-10 space-y-6">
      <!-- Back button -->
      <button
        @click="goHome"
        class="inline-flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-blue-600 transition cursor-pointer border-none bg-transparent outline-none"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Home
      </button>

      <!-- Header -->
      <div class="border-b border-gray-100 pb-5">
        <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">Privacy Policy</h1>
        <p class="text-xs text-gray-400 mt-1">Last Updated: June 2026</p>
      </div>

      <!-- Policy Content -->
      <div class="prose prose-sm max-w-none text-gray-700 space-y-6 leading-relaxed">
        <p class="text-sm">
          Welcome to <strong>NxtTurn</strong>. Your privacy and data security are our highest
          priorities. This Privacy Policy describes how we collect, use, and safeguard your personal
          information when you use our professional student and alumni networking platform.
        </p>

        <!-- Section 1 -->
        <div class="space-y-2">
          <h2 class="text-lg font-bold text-gray-900">1. Information We Collect</h2>
          <p class="text-sm">
            When you create an account, complete your profile, or interact with others on NxtTurn,
            we collect several types of information:
          </p>
          <ul class="list-disc pl-5 space-y-1 text-sm">
            <li>
              <strong>Account Credentials:</strong> Your username, email address, and encrypted
              passwords.
            </li>
            <li>
              <strong>Profile Details:</strong> Your biography, educational history, work
              experience, skill categories, and uploaded resume files.
            </li>
            <li>
              <strong>User-Generated Content:</strong> Your posts, comments, likes, reactions, and
              direct messages.
            </li>
          </ul>
        </div>

        <!-- Section 2 -->
        <div class="space-y-2 pt-2">
          <h2 class="text-lg font-bold text-gray-900">2. Guest Browser & Public Visibility</h2>
          <p class="text-sm">
            To drive search engine optimization (SEO) and professional discoverability, NxtTurn
            allows unauthenticated visitors (guests) and search engines to read public content.
          </p>
          <p class="text-sm">
            However, we protect your personal credentials using our advanced
            <strong>Dual-Lock Shield</strong>:
          </p>
          <ul class="list-disc pl-5 space-y-1 text-sm">
            <li>
              If your profile is set to <strong>Public</strong>, guests can see your basic name,
              photo, and public posts. However, your email, phone, and resume are strictly masked.
            </li>
            <li>
              If your profile is set to <strong>Private</strong> (Members, Followers, or
              Connections), guests are blocked from seeing any of your details and are greeted with
              a locked shield screen.
            </li>
            <li>
              Guests can read public posts on the explore feed, but they cannot perform write
              operations (like liking, commenting, or connecting) without registering.
            </li>
          </ul>
        </div>

        <!-- Section 3 -->
        <div class="space-y-2 pt-2">
          <h2 class="text-lg font-bold text-gray-900">3. Your Privacy Controls</h2>
          <p class="text-sm">
            You have complete control over your data. Through your dedicated
            <strong>Privacy & Safety</strong> settings panel, you can choose exactly who is
            authorized to view your profile details, contact information, and inbox:
          </p>
          <ul class="list-disc pl-5 space-y-1 text-sm">
            <li>
              <strong>Everyone:</strong> Open to all members and unauthenticated public guests.
            </li>
            <li><strong>Registered Members:</strong> Open only to logged-in NxtTurn users.</li>
            <li><strong>My Followers:</strong> Restricted to users who follow you.</li>
            <li>
              <strong>Mutual Connections:</strong> Restricted strictly to approved mutual
              connections.
            </li>
            <li><strong>Only Me:</strong> Fully private; only you can view this data.</li>
          </ul>
        </div>

        <!-- Section 4 -->
        <div class="space-y-2 pt-2">
          <h2 class="text-lg font-bold text-gray-900">4. Data Security</h2>
          <p class="text-sm">
            We use industry-standard encryption, token authentications, and secure storage adapters
            to protect your files and data transmission. Your database transactions are heavily
            secured, and resume uploads are locked using random, cryptographically-secure UUIDs to
            prevent unauthorized scraping.
          </p>
        </div>
      </div>

      <!-- Bottom CTA -->
      <div class="border-t border-gray-100 pt-6 flex justify-center">
        <button
          @click="goHome"
          class="px-8 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-bold text-sm rounded-full shadow hover:shadow-md transition active:scale-95 text-center cursor-pointer"
        >
          Start Browsing NxtTurn
        </button>
      </div>
    </div>
  </div>
</template>
