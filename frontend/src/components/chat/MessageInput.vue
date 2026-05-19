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
        class="mx-1 rounded-[1.5rem] border border-indigo-200 bg-indigo-50/90 px-4 py-3 text-xs font-semibold text-indigo-800 shadow-sm backdrop-blur-md"
      >
        <div class="flex items-center justify-between gap-3">
          <div class="min-w-0">
            <div class="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-600">
              Replying to {{ replyingMessage?.sender_username || 'message' }}
            </div>
            <div class="truncate text-sm font-medium text-indigo-900/80">
              {{ replyingMessage?.content || 'Media message' }}
            </div>
          </div>
          <button
            class="rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-indigo-700 transition hover:bg-indigo-100"
            type="button"
            @click="$emit('cancel-reply')"
          >
            Cancel
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
      <div v-if="attachments.length && !isEditing" class="mx-1 rounded-[2rem] border border-white/70 bg-white/80 p-4 shadow-lg shadow-blue-100 backdrop-blur-2xl">
        <div class="mb-4 flex items-center justify-between px-2">
          <div class="flex items-center gap-2">
            <span class="h-2 w-2 rounded-full bg-blue-500"></span>
            <span class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Attached Media</span>
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
              class="h-16 w-16 rounded-[1rem] object-cover shadow-sm ring-1 ring-blue-100 transition-transform duration-500 group-hover:scale-105"
            />
            <div v-else-if="attachment.kind === 'video'" class="grid h-16 w-16 place-items-center rounded-[1rem] bg-gradient-to-br from-blue-600 to-indigo-600 shadow-sm">
              <div class="grid h-9 w-9 place-items-center rounded-full bg-white/15 backdrop-blur-md">
                <svg class="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                </svg>
              </div>
            </div>
            <div class="min-w-0 flex-1">
              <div class="truncate text-sm font-semibold text-slate-800">{{ attachment.file.name }}</div>
              <div class="mt-0.5 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
                {{ attachment.kind }} ready to send
              </div>
            </div>
            <button
              class="grid h-8 w-8 place-items-center rounded-full bg-rose-500 text-white shadow-lg transition-all duration-200 hover:scale-110"
              type="button"
              @click="removeAttachment(index)"
            >
              <svg class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
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

    <div class="group relative flex items-end gap-3 px-1">
      <div class="relative flex flex-1 flex-col gap-2">
        <div class="relative">
          <textarea
            ref="inputArea"
            v-model="message"
            :disabled="disabled"
            rows="1"
            :placeholder="isEditing ? 'Edit your message...' : 'Type a message...'"
            class="custom-scrollbar w-full max-h-32 resize-none rounded-[2rem] bg-white/90 py-4 pl-14 pr-14 text-[15px] font-medium leading-relaxed text-slate-800 shadow-sm outline-none transition-all placeholder:text-slate-400 hover:bg-white focus:shadow-md focus:ring-4 focus:ring-blue-500/10 disabled:opacity-50"
            @input="adjustHeight"
            @keydown.enter.prevent="send"
          ></textarea>

          <button
            class="absolute left-3 bottom-2 flex h-11 w-11 items-center justify-center rounded-[1.25rem] text-slate-400 transition-all duration-300 hover:bg-blue-50 hover:text-blue-600 active:scale-90"
            :disabled="disabled || isEditing"
            type="button"
            @click="openFilePicker"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>

          <div class="absolute right-3 bottom-2">
            <button
              class="flex h-11 w-11 items-center justify-center rounded-[1.25rem] text-2xl transition-all duration-300 hover:bg-violet-50 hover:scale-110 active:scale-90"
              :disabled="disabled || isEditing"
              type="button"
              @click="toggleEmoji"
            >
              😊
            </button>

            <transition
              enter-active-class="transition duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
              enter-from-class="translate-y-8 opacity-0 scale-90"
              enter-to-class="translate-y-0 opacity-100 scale-100"
              leave-active-class="transition duration-200 ease-in"
              leave-from-class="translate-y-0 opacity-100 scale-100"
              leave-to-class="translate-y-4 opacity-0 scale-95"
            >
              <div
                v-if="showEmoji"
                class="absolute bottom-14 right-0 z-[100] w-80 rounded-[2.5rem] bg-white/95 p-5 shadow-2xl shadow-blue-100 backdrop-blur-3xl"
              >
                <div class="mb-4 flex gap-2 overflow-x-auto border-b border-slate-100 pb-1 no-scrollbar">
                  <button
                    v-for="cat in Object.keys(emojiCategories)"
                    :key="cat"
                    class="whitespace-nowrap px-2 py-1 text-[10px] font-black uppercase tracking-tighter transition-colors"
                    :class="activeCategory === cat ? 'text-blue-600' : 'text-slate-400 hover:text-slate-600'"
                    type="button"
                    @click="activeCategory = cat"
                  >
                    {{ cat }}
                  </button>
                </div>

                <div class="custom-scrollbar grid max-h-56 grid-cols-6 gap-2 overflow-y-auto pr-1">
                  <button
                    v-for="emoji in emojiCategories[activeCategory]"
                    :key="emoji"
                    class="flex h-10 w-10 items-center justify-center rounded-xl text-xl transition-all duration-200 hover:bg-blue-50 hover:scale-125 active:scale-90"
                    type="button"
                    @click="pickEmoji(emoji)"
                  >
                    {{ emoji }}
                  </button>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>

      <button
        class="group/send relative flex h-14 w-14 items-center justify-center rounded-[1.5rem] bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20 transition-all duration-300 hover:from-blue-700 hover:to-indigo-700 active:scale-95 disabled:opacity-40"
        :disabled="disabled || (!message.trim() && !attachments.length)"
        type="button"
        @click="send"
      >
        <svg class="h-6 w-6 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
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
      <div v-if="errorMessage" class="mx-4 flex items-center gap-2 rounded-xl bg-rose-50 px-3 py-2 text-[10px] font-black uppercase tracking-widest text-rose-500">
        <span class="h-1 w-1 rounded-full bg-rose-500"></span>
        {{ errorMessage }}
      </div>
    </transition>
  </div>
</template>

<script>
import { EMOJI_CATEGORIES } from './emojis'

export default {
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
    editingMessage: {
      type: Object,
      default: null,
    },
    replyingMessage: {
      type: Object,
      default: null,
    },
  },
  emits: ['send', 'cancel-edit', 'cancel-reply'],
  data() {
    return {
      message: '',
      attachments: [],
      showEmoji: false,
      activeCategory: 'Popular',
      emojiCategories: EMOJI_CATEGORIES,
      errorMessage: '',
    }
  },
  computed: {
    isEditing() {
      return Boolean(this.editingMessage)
    },
    isReplying() {
      return Boolean(this.replyingMessage)
    },
  },
  watch: {
    attachments: {
      handler(newFiles, oldFiles) {
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
      handler(val) {
        this.errorMessage = ''
        this.showEmoji = false
        this.clearFiles()
        this.message = val?.content || ''
        this.$nextTick(() => this.adjustHeight())
      },
    },
  },
  beforeUnmount() {
    this.attachments.forEach((attachment) => {
      if (attachment.previewUrl) {
        URL.revokeObjectURL(attachment.previewUrl)
      }
    })
  },
  methods: {
    adjustHeight() {
      const el = this.$refs.inputArea
      if (el) {
        el.style.height = 'auto'
        el.style.height = `${el.scrollHeight}px`
      }
    },
    openFilePicker() {
      if (this.disabled || this.isEditing) return
      this.$refs.fileInput?.click()
    },
    onFileChange(event) {
      if (this.isEditing) return
      const files = Array.from(event.target?.files || [])
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
        kind: file.type.startsWith('image/') ? 'image' : file.type.startsWith('video/') ? 'video' : 'file',
        previewUrl: file.type.startsWith('image/') || file.type.startsWith('video/') ? URL.createObjectURL(file) : '',
      }))
    },
    toggleEmoji() {
      if (this.disabled || this.isEditing) return
      this.showEmoji = !this.showEmoji
    },
    pickEmoji(emoji) {
      this.message = `${this.message}${emoji}`
      this.$nextTick(() => this.adjustHeight())
    },
    removeAttachment(index) {
      const [removed] = this.attachments.splice(index, 1)
      if (removed?.previewUrl) {
        URL.revokeObjectURL(removed.previewUrl)
      }
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
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
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
      this.errorMessage = ''
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
      this.$nextTick(() => {
        if (this.$refs.inputArea) this.$refs.inputArea.style.height = 'auto'
      })
      this.clearFiles()
      this.showEmoji = false
    },
  },
}
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

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
