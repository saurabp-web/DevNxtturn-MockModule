<template>
  <img
    :src="displayedSrc || src"
    :alt="alt"
    v-bind="$attrs"
  />
</template>

<script>
export default {
  inheritAttrs: false,
  props: {
    src: {
      type: String,
      default: '',
    },
    alt: {
      type: String,
      default: 'user avatar',
    },
  },
  data() {
    return {
      displayedSrc: this.src,
      loadToken: 0,
    }
  },
  watch: {
    src: {
      immediate: true,
      handler(nextSrc) {
        if (!nextSrc || nextSrc === this.displayedSrc) return
        if (nextSrc.startsWith('data:')) {
          this.displayedSrc = nextSrc
          return
        }

        const token = this.loadToken + 1
        this.loadToken = token

        const image = new Image()
        image.onload = () => {
          if (token === this.loadToken) {
            this.displayedSrc = nextSrc
          }
        }
        image.onerror = () => {
          if (!this.displayedSrc && token === this.loadToken) {
            this.displayedSrc = nextSrc
          }
        }
        image.src = nextSrc
      },
    },
  },
}
</script>
