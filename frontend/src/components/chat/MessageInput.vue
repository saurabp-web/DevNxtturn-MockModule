<template>
  <div class="flex flex-col gap-4">
    <transition
      enter-active-class="transition duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
      enter-from-class="translate-y-8 opacity-0 scale-90"
      enter-to-class="translate-y-0 opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="translate-y-0 opacity-100 scale-100"
      leave-to-class="translate-y-4 opacity-0 scale-95"
    >
      <div
        v-if="isReplying"
        class="mx-1 overflow-hidden rounded-[1.35rem] border border-violet-100/80 bg-white/95 text-xs shadow-sm shadow-violet-100/50 backdrop-blur-md"
      >
        <div class="flex items-stretch justify-between gap-3">
          <div class="flex min-w-0 flex-1 gap-3 px-4 py-3">
            <div
              class="w-1 flex-shrink-0 rounded-full"
              :class="replyingMessage?.is_deleted ? 'bg-slate-300' : 'bg-violet-500'"
            ></div>
            <div class="min-w-0 flex-1">
              <div
                class="mt-0.5 truncate text-sm font-bold"
                :class="replyingMessage?.is_deleted ? 'text-slate-500' : 'text-violet-700'"
              >
                {{ replyingSenderName }}
              </div>
              <div
                class="mt-0.5 truncate text-sm font-medium"
                :class="replyingMessage?.is_deleted ? 'italic text-slate-400' : 'text-slate-700'"
              >
                {{ replyPreviewText }}
              </div>
            </div>
            <div
              v-if="replyPreviewMedia"
              class="h-12 w-12 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 ring-1 ring-slate-200"
            >
              <img
                v-if="replyPreviewMedia.kind !== 'video'"
                :src="replyPreviewMedia.url"
                alt=""
                class="h-full w-full object-cover"
              />
              <video
                v-else
                :src="replyPreviewMedia.url"
                class="h-full w-full object-cover"
                muted
                playsinline
                preload="metadata"
              ></video>
            </div>
          </div>
          <button
            class="my-2 mr-2 grid h-9 w-9 flex-shrink-0 place-items-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            type="button"
            aria-label="Cancel reply"
            @click="$emit('cancel-reply')"
          >
            <svg
              class="h-4 w-4"
              fill="none"
              stroke="currentColor"
              stroke-width="2.4"
              viewBox="0 0 24 24"
            >
              <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
            </svg>
          </button>
        </div>
      </div>
    </transition>

    <transition
      enter-active-class="transition duration-400 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
      enter-from-class="translate-y-8 opacity-0 scale-90"
      enter-to-class="translate-y-0 opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="translate-y-0 opacity-100 scale-100"
      leave-to-class="translate-y-4 opacity-0 scale-95"
    >
      <div
        v-if="attachments.length && !isEditing"
        class="mx-1 rounded-[2rem] border border-violet-100/70 bg-white/85 p-4 shadow-lg shadow-violet-100 backdrop-blur-2xl"
      >
        <div class="mb-4 flex items-center justify-between px-2">
          <div class="flex items-center gap-2">
            <span class="h-2 w-2 rounded-full bg-violet-500"></span>
            <span class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500"
              >Attached Media</span
            >
          </div>
        </div>

        <div class="px-1">
          <div
            v-for="(attachment, index) in attachments"
            :key="`${attachment.file.name}-${index}`"
            class="group relative flex min-h-24 items-center gap-4 overflow-hidden rounded-[1.5rem] bg-white p-3 transition-all duration-300 hover:-translate-y-0.5 ring-1 ring-slate-100"
          >
            <img
              v-if="attachment.kind === 'image'"
              :src="attachment.previewUrl"
              class="h-16 w-16 rounded-[1rem] object-cover shadow-sm ring-1 ring-violet-100 transition-transform duration-500 group-hover:scale-105"
            />
            <div
              v-else-if="attachment.kind === 'video'"
              class="grid h-16 w-16 place-items-center rounded-[1rem] bg-gradient-to-br from-violet-600 to-fuchsia-600 shadow-sm"
            >
              <div
                class="grid h-9 w-9 place-items-center rounded-full bg-white/15 backdrop-blur-md"
              >
                <svg class="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"
                  />
                </svg>
              </div>
            </div>
            <div class="min-w-0 flex-1">
              <div class="truncate text-sm font-semibold text-slate-800">
                {{ attachment.file.name }}
              </div>
              <div class="mt-0.5 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
                {{ attachment.kind }} ready to send
              </div>
            </div>
            <button
              class="grid h-8 w-8 place-items-center rounded-full bg-rose-500 text-white shadow-lg transition-all duration-200 hover:scale-110"
              type="button"
              @click="removeAttachment(index)"
            >
              <svg
                class="h-3 w-3"
                fill="none"
                stroke="currentColor"
                stroke-width="3"
                viewBox="0 0 24 24"
              >
                <path d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-if="isEditing"
        class="mx-1 flex items-center justify-between rounded-[1.5rem] border border-amber-200 bg-amber-50/90 px-4 py-3 text-xs font-semibold text-amber-800 shadow-sm backdrop-blur-md"
      >
        <div class="flex items-center gap-2">
          <span class="h-2 w-2 rounded-full bg-amber-500"></span>
          <span>Editing message</span>
        </div>
        <button
          class="rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-amber-700 transition hover:bg-amber-100"
          type="button"
          @click="$emit('cancel-edit')"
        >
          Cancel
        </button>
      </div>
    </transition>

    <div class="group relative flex items-end gap-2 px-0.5 sm:gap-3 sm:px-1">
      <div class="relative flex flex-1 flex-col gap-2">
        <div class="relative">
          <textarea
            ref="inputArea"
            v-model="message"
            :disabled="disabled"
            rows="1"
            :placeholder="isEditing ? 'Edit your message...' : 'Type a message...'"
            class="custom-scrollbar w-full max-h-32 resize-none rounded-[1.55rem] border border-violet-100/80 bg-white/95 py-3.5 pl-12 pr-12 text-[15px] font-medium leading-relaxed text-slate-800 shadow-sm shadow-violet-100/40 outline-none transition-all placeholder:text-slate-400 hover:bg-white focus:border-violet-200 focus:shadow-md focus:shadow-violet-100 focus:ring-4 focus:ring-violet-500/10 disabled:opacity-50 sm:rounded-[2rem] sm:py-4 sm:pl-14 sm:pr-14"
            @input="handleInput"
            @keydown="handleKeydown"
            @focus="handleFocus"
            @keydown.enter.prevent="send"
            @blur="handleBlur"
          ></textarea>

          <button
            class="absolute left-2 bottom-2 flex h-10 w-10 items-center justify-center rounded-[1.1rem] text-violet-400 transition-all duration-300 hover:bg-violet-50 hover:text-violet-600 active:scale-90 sm:left-3 sm:h-11 sm:w-11 sm:rounded-[1.25rem]"
            :disabled="disabled || isEditing"
            type="button"
            @click="openFilePicker"
          >
            <svg
              class="h-6 w-6"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </button>

          <div class="absolute right-3 bottom-2">
            <button
              ref="emojiButton"
              class="flex h-10 w-10 items-center justify-center rounded-[1.1rem] bg-violet-50/70 text-2xl shadow-sm shadow-violet-100/60 ring-1 ring-violet-100/70 transition-all duration-300 hover:bg-violet-100/80 hover:scale-110 hover:shadow-violet-200 active:scale-90 sm:h-11 sm:w-11 sm:rounded-[1.25rem]"
              :disabled="disabled || isEditing"
              type="button"
              @click="toggleEmoji"
              aria-label="Open emoji picker"
            >
              <svg class="h-6 w-6 text-violet-500" fill="none" viewBox="0 0 24 24">
                <path
                  d="M12 20.25c4.556 0 8.25-3.694 8.25-8.25S16.556 3.75 12 3.75 3.75 7.444 3.75 12c0 1.56.44 3.015 1.2 4.25L4 20l3.75-.95c1.22.75 2.65 1.2 4.25 1.2z"
                  fill="currentColor"
                  fill-opacity="0.12"
                />
                <path
                  d="M9.25 9.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0zm7 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0z"
                  fill="currentColor"
                />
                <path
                  d="M8.2 13.75c.95 1.1 2.1 1.65 3.8 1.65s2.85-.55 3.8-1.65"
                  stroke="currentColor"
                  stroke-width="1.7"
                  stroke-linecap="round"
                />
                <path
                  d="M18.7 5.4l-.55-1.47L16.7 3.4l1.45-.53.55-1.47.55 1.47 1.45.53-1.45.53-.55 1.47z"
                  fill="currentColor"
                  opacity=".55"
                />
                <path
                  d="M8.5 15.7c.9.8 2.1 1.2 3.5 1.2s2.6-.4 3.5-1.2"
                  stroke="currentColor"
                  stroke-width="1.1"
                  stroke-linecap="round"
                  opacity=".45"
                />
              </svg>
            </button>

            <teleport to="body">
              <transition
                enter-active-class="transition duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
                enter-from-class="translate-y-8 opacity-0 scale-90"
                enter-to-class="translate-y-0 opacity-100 scale-100"
                leave-active-class="transition duration-200 ease-in"
                leave-from-class="translate-y-0 opacity-100 scale-100"
                leave-to-class="translate-y-4 opacity-0 scale-95"
              >
                <div v-if="showEmoji" class="fixed z-[260]" :style="emojiPanelStyle" @click.stop>
                  <EmojiPicker
                    :open="showEmoji"
                    mode="composer"
                    @select="pickEmoji"
                    @pick-media="pickMedia"
                    @close="showEmoji = false"
                  />
                </div>
              </transition>
            </teleport>
          </div>
        </div>
      </div>

      <button
        class="group/send relative flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-[1.25rem] bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/25 transition-all duration-300 hover:from-violet-700 hover:to-fuchsia-700 hover:shadow-violet-500/30 active:scale-95 disabled:opacity-40 sm:h-14 sm:w-14 sm:rounded-[1.5rem]"
        :disabled="disabled || (!message.trim() && !attachments.length)"
        type="button"
        @click="send"
      >
        <svg
          class="h-6 w-6 transition-transform group-hover:translate-x-1"
          fill="none"
          stroke="currentColor"
          stroke-width="3"
          viewBox="0 0 24 24"
        >
          <path d="M5 12h14m-7-7l7 7-7 7" />
        </svg>
      </button>

      <input
        ref="fileInput"
        class="hidden"
        type="file"
        accept="image/*,video/*"
        :disabled="disabled || isEditing"
        @change="onFileChange"
      />
    </div>

    <transition name="fade">
      <div
        v-if="errorMessage"
        class="mx-4 flex items-center gap-2 rounded-xl bg-rose-50 px-3 py-2 text-[10px] font-black uppercase tracking-widest text-rose-500"
      >
        <span class="h-1 w-1 rounded-full bg-rose-500"></span>
        {{ errorMessage }}
      </div>
    </transition>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import EmojiPicker from './EmojiPicker.vue'
import { buildMediaUrl } from '@/utils/avatars'

export default defineComponent({
  components: {
    EmojiPicker,
  },
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
    draftText: {
      type: String,
      default: '',
    },
    editingMessage: {
      type: Object,
      default: null,
    },
    replyingMessage: {
      type: Object,
      default: null,
    },
    currentUserId: {
      type: [Number, String],
      default: '',
    },
  },
  emits: ['send', 'cancel-edit', 'cancel-reply', 'typing', 'draft-change'],
  data() {
    return {
      message: '',
      attachments: [] as any[],
      showEmoji: false,
      emojiPanelStyle: {
        left: '0px',
        top: '0px',
        width: '28rem',
        height: '60vh',
      },
      errorMessage: '',
      lastTypingState: false,
      typingIdleTimer: null as any,
    }
  },
  computed: {
    isEditing(): boolean {
      return Boolean(this.editingMessage)
    },
    isReplying(): boolean {
      return Boolean(this.replyingMessage)
    },
    replyPreviewText(): string {
      if (this.replyingMessage?.is_deleted) return 'Message deleted'
      const type = String(
        this.replyingMessage?.message_type || this.replyingMessage?.type || 'text',
      ).toLowerCase()
      if (type === 'gif') return 'GIF'
      if (type === 'sticker') return 'Sticker'
      if (this.replyingMessage?.content?.trim()) return this.replyingMessage.content.trim()
      if (this.replyPreviewMedia?.kind === 'video') return 'Video'
      if (this.replyPreviewMedia?.kind === 'image') return 'Photo'
      return 'Message'
    },
    replyPreviewMedia(): any {
      const message = this.replyingMessage
      if (!message || message.is_deleted) return null
      const type = String(message?.message_type || message?.type || 'text').toLowerCase()
      const mediaType = String(message?.media_type || '').toLowerCase()
      const preview =
        message?.media_preview || message?.preview || message?.last_message_preview || null
      const raw =
        type === 'gif'
          ? message?.gif_url || message?.external_url || preview?.url || ''
          : type === 'sticker'
            ? message?.sticker_url || message?.external_url || preview?.url || ''
            : message?.media_url || message?.media || preview?.url || ''
      const url = buildMediaUrl(raw || '')
      if (!url) return null
      if (type === 'gif') return { kind: 'gif', url }
      if (type === 'sticker') return { kind: 'sticker', url }
      const isVideo =
        preview?.kind === 'video' ||
        mediaType.startsWith('video/') ||
        /\.(mp4|webm|ogg|mov)(\?|#|$)/i.test(String(url))
      return { kind: isVideo ? 'video' : 'image', url }
    },
    replyingSenderName(): string {
      if (String(this.replyingSenderId) === String(this.currentUserId ?? '')) {
        return 'You'
      }
      return (
        this.replyingMessage?.sender_display_name ||
        this.replyingMessage?.sender_username ||
        this.replyingMessage?.sender?.username ||
        this.replyingMessage?.sender_user?.username ||
        'Message'
      )
    },
    replyingSenderId(): string | number {
      const sender = this.replyingMessage?.sender
      if (sender && typeof sender === 'object') {
        return sender.id ?? sender.user_id ?? sender.pk ?? ''
      }
      return this.replyingMessage?.sender_id ?? sender ?? ''
    },
  },
  watch: {
    attachments: {
      handler(newFiles: any[], oldFiles: any[]) {
        const oldUrls = (oldFiles || []).map((item) => item.previewUrl)
        const currentUrls = (newFiles || []).map((item) => item.previewUrl)
        oldUrls.forEach((url) => {
          if (!currentUrls.includes(url)) {
            URL.revokeObjectURL(url)
          }
        })
      },
      deep: true,
    },
    editingMessage: {
      immediate: true,
      handler(val: any) {
        this.errorMessage = ''
        this.showEmoji = false
        this.clearFiles()
        this.message = val?.content || this.draftText || ''
        this.$nextTick(() => this.adjustHeight())
        this.syncTypingState(true)
      },
    },
    draftText: {
      immediate: true,
      handler(val: string) {
        if (this.isEditing) return
        const nextValue = val || ''
        if (nextValue !== this.message) {
          this.message = nextValue
          this.$nextTick(() => this.adjustHeight())
        }
      },
    },
    message() {
      this.$nextTick(() => this.adjustHeight())
      this.syncTypingState()
    },
    disabled() {
      this.syncTypingState(true)
    },
    showEmoji(isOpen: boolean) {
      if (!isOpen) {
        window.removeEventListener('resize', this.repositionEmojiPanel)
        window.removeEventListener('scroll', this.repositionEmojiPanel, true)
        return
      }

      this.$nextTick(() => {
        this.repositionEmojiPanel()
        window.addEventListener('resize', this.repositionEmojiPanel)
        window.addEventListener('scroll', this.repositionEmojiPanel, true)
      })
    },
  },
  beforeUnmount() {
    if (this.typingIdleTimer) {
      clearTimeout(this.typingIdleTimer)
      this.typingIdleTimer = null
    }
    this.attachments.forEach((attachment) => {
      if (attachment.previewUrl) {
        URL.revokeObjectURL(attachment.previewUrl)
      }
    })
    window.removeEventListener('resize', this.repositionEmojiPanel)
    window.removeEventListener('scroll', this.repositionEmojiPanel, true)
  },
  methods: {
    syncTypingState(force: boolean = false) {
      const isTyping = Boolean(this.message?.trim()) && !this.disabled && !this.isEditing
      if (force || isTyping !== this.lastTypingState) {
        this.lastTypingState = isTyping
        this.$emit('typing', isTyping)
      }
      if (this.typingIdleTimer) {
        clearTimeout(this.typingIdleTimer)
        this.typingIdleTimer = null
      }
      if (isTyping) {
        this.typingIdleTimer = window.setTimeout(() => {
          this.typingIdleTimer = null
          this.lastTypingState = false
          this.$emit('typing', false)
        }, 1800)
      }
    },
    handleInput() {
      this.$emit('draft-change', this.message)
      this.syncTypingState()
    },
    handleKeydown(event: any) {
      if (event?.key === 'Enter') return
      this.syncTypingState(true)
    },
    handleFocus() {
      this.syncTypingState()
    },
    handleBlur() {
      if (this.typingIdleTimer) {
        clearTimeout(this.typingIdleTimer)
        this.typingIdleTimer = null
      }
      this.lastTypingState = false
      this.$emit('typing', false)
    },
    adjustHeight() {
      const el = this.$refs.inputArea as HTMLTextAreaElement | null
      if (el) {
        el.style.height = 'auto'
        el.style.height = `${el.scrollHeight}px`
      }
    },
    openFilePicker() {
      if (this.disabled || this.isEditing) return
      ;(this.$refs.fileInput as HTMLInputElement | null)?.click()
    },
    onFileChange(event: any) {
      if (this.isEditing) return
      const files = Array.from(event.target?.files || []) as File[]
      if (!files.length) return

      if (files.length > 1) {
        this.errorMessage = 'Send 1 image or 1 video at a time'
        event.target.value = ''
        return
      }

      const imageFiles = files.filter((file) => file.type.startsWith('image/'))
      const videoFiles = files.filter((file) => file.type.startsWith('video/'))
      const invalidFiles = files.length - imageFiles.length - videoFiles.length

      if (invalidFiles > 0) {
        this.errorMessage = 'Images and Videos only'
        event.target.value = ''
        return
      }

      if (imageFiles.length > 1 || videoFiles.length > 1) {
        this.errorMessage = 'Send 1 image or 1 video at a time'
        event.target.value = ''
        return
      }

      this.errorMessage = ''
      this.attachments = files.map((file) => ({
        file,
        kind: file.type.startsWith('image/')
          ? 'image'
          : file.type.startsWith('video/')
            ? 'video'
            : 'file',
        previewUrl:
          file.type.startsWith('image/') || file.type.startsWith('video/')
            ? URL.createObjectURL(file)
            : '',
      }))
    },
    toggleEmoji() {
      if (this.disabled || this.isEditing) return
      this.showEmoji = !this.showEmoji
    },
    openEmojiPicker() {
      if (this.disabled || this.isEditing) return
      this.showEmoji = true
      this.$nextTick(() => {
        this.focusInputWithoutScroll()
      })
    },
    repositionEmojiPanel() {
      const button = this.$refs.emojiButton
      if (!(button instanceof HTMLElement)) return

      const rect = button.getBoundingClientRect()
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight
      const panelWidth = Math.min(420, Math.max(280, viewportWidth - 20))
      const panelHeight = Math.min(
        Math.max(420, Math.round(viewportHeight * 0.7)),
        viewportHeight - 16,
      )
      const gutter = 12

      const left = Math.max(
        gutter,
        Math.min(rect.right - panelWidth, viewportWidth - panelWidth - gutter),
      )
      const aboveTop = rect.top - panelHeight - gutter
      const belowTop = rect.bottom + gutter
      const top =
        aboveTop >= gutter ? aboveTop : Math.min(belowTop, viewportHeight - panelHeight - gutter)

      this.emojiPanelStyle = {
        left: `${left}px`,
        top: `${Math.max(gutter, top)}px`,
        width: `${panelWidth}px`,
        height: `${panelHeight}px`,
      }
    },
    pickEmoji(emoji: string) {
      if (!emoji) return
      this.message = `${this.message}${emoji}`
      this.$emit('draft-change', this.message)
      this.$nextTick(() => this.adjustHeight())
      this.$nextTick(() => this.focusInputWithoutScroll())
    },
    pickMedia(item: any) {
      if (!item || this.disabled || this.isEditing) return
      if (!item.sendUrl) return

      this.$emit('send', {
        text: '',
        files: [],
        editingMessageId: this.editingMessage?.id || null,
        replyToMessageId: this.replyingMessage?.id || null,
        media: {
          kind: item.kind,
          title: item.title,
          provider: item.provider,
          providerId: item.providerId,
          previewUrl: item.previewUrl,
          sendUrl: item.sendUrl,
          stillUrl: item.stillUrl,
          animated: item.animated,
        },
      })

      this.message = ''
      this.$emit('draft-change', '')
      this.lastTypingState = false
      if (this.typingIdleTimer) {
        clearTimeout(this.typingIdleTimer)
        this.typingIdleTimer = null
      }
      this.$emit('typing', false)
      this.$nextTick(() => {
        const inputArea = this.$refs.inputArea as HTMLTextAreaElement | null
        if (inputArea) inputArea.style.height = 'auto'
      })
      this.clearFiles()
      this.showEmoji = false
    },
    removeAttachment(index: number) {
      const [removed] = this.attachments.splice(index, 1)
      if (removed?.previewUrl) {
        URL.revokeObjectURL(removed.previewUrl)
      }
      const fileInput = this.$refs.fileInput as HTMLInputElement | null
      if (fileInput) {
        fileInput.value = ''
      }
      this.errorMessage = ''
    },
    clearFiles() {
      this.attachments.forEach((attachment) => {
        if (attachment.previewUrl) {
          URL.revokeObjectURL(attachment.previewUrl)
        }
      })
      this.attachments = []
      const fileInput = this.$refs.fileInput as HTMLInputElement | null
      if (fileInput) {
        fileInput.value = ''
      }
      this.errorMessage = ''
    },
    focusInputWithoutScroll() {
      const input = this.$refs.inputArea as HTMLTextAreaElement | null
      if (!input || typeof input.focus !== 'function') return
      try {
        input.focus({ preventScroll: true })
      } catch {
        input.focus()
      }
    },
    send() {
      if (this.disabled || (!this.message.trim() && !this.attachments.length)) return
      this.$emit('send', {
        text: this.message.trim(),
        files: this.attachments.map((attachment) => attachment.file),
        editingMessageId: this.editingMessage?.id || null,
        replyToMessageId: this.replyingMessage?.id || null,
      })
      this.message = ''
      this.$emit('draft-change', '')
      this.lastTypingState = false
      if (this.typingIdleTimer) {
        clearTimeout(this.typingIdleTimer)
        this.typingIdleTimer = null
      }
      this.$emit('typing', false)
      this.$nextTick(() => {
        const inputArea = this.$refs.inputArea as HTMLTextAreaElement | null
        if (inputArea) inputArea.style.height = 'auto'
      })
      this.clearFiles()
      this.showEmoji = false
    },
  },
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #f1f5f9;
  border-radius: 10px;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
