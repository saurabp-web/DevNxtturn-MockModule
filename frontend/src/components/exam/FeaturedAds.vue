<template>
  <aside class="panel">
    <h3>Featured Ads &amp; Course Packs</h3>

    <div class="ad-card" style="background:#fce7f3">
      <div class="ad-label">Prep Course</div>
      <div class="ad-title">UPSC Comprehensive Prep Course</div>
      <div class="ad-subtitle">UPSC Comprehensive Course</div>
      <div class="ad-footer">
        <span class="ad-price">₹3.99</span>
        <button class="ad-buy-btn" style="color:#ec4899">Buy Now</button>
      </div>
    </div>

    <div class="ad-card" style="background:#ede9fe">
      <div class="ad-title">SSC CGL Crash Course</div>
      <div class="ad-subtitle">SSC CGL Crash Course preparation</div>
      <button class="ad-buy-btn" style="color:#7c3aed">Buy Now</button>
    </div>

    <div class="ads-row">
      <div class="ad-card-small" style="background:#fef3c7">
        <div class="ad-small-label">Monthly Subscription Deal</div>
        <div class="ad-small-title">Get any subscription prep course</div>
        <button class="ad-buy-btn" style="color:#f59e0b">Buy Now</button>
      </div>
      <div class="ad-card-small" style="background:#dbeafe">
        <div class="ad-small-label">Test Series Bundle</div>
        <div class="ad-small-title">Test series bundle</div>
        <button class="ad-buy-btn" style="color:#3b82f6">Get Now</button>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.panel {
  background: #f3f1fb;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}

.panel h3 {
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 14px;
  color: #1e2536;
}

/* Large ad cards */
.ad-card {
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 14px;
}

.ad-label {
  font-size: 10px;
  font-weight: 700;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 4px;
}

.ad-title {
  font-size: 13px;
  font-weight: 700;
  color: #1e2536;
  line-height: 1.35;
  margin-bottom: 3px;
  word-break: break-word;
}

.ad-subtitle {
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 10px;
  line-height: 1.4;
}

.ad-footer {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ad-price {
  font-size: 14px;
  font-weight: 700;
  color: #1e2536;
}

.ad-buy-btn {
  background: #fff;
  border: none;
  padding: 5px 13px;
  border-radius: 7px;
  font-weight: 700;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}

/* Small side-by-side cards */
.ads-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.ad-card-small {
  border-radius: 12px;
  padding: 12px 10px;
}

.ad-small-label {
  font-size: 10px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 4px;
  line-height: 1.3;
}

.ad-small-title {
  font-size: 13px;
  font-weight: 700;
  color: #1e2536;
  line-height: 1.3;
  margin-bottom: 10px;
}
</style>