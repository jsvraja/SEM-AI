path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Fix 1: Disclaimer text
old = '⚠ Scores based on raw HTML. JS-rendered sites may show different values. Click &quot;Google Score&quot; for full accuracy.'
new = '⚠ These are our tool\'s scores based on raw HTML analysis. Compare with performance analysis for full accuracy.'

content = content.replace(
    'Scores based on raw HTML. JS-rendered sites may show different values. Click "Google Score" for full accuracy.',
    'These are our tool\'s scores based on raw HTML analysis. Compare with performance analysis for full accuracy.'
)

# Fix 2: Better score calculation based on actual scraped data
old_breakdown = """                  const seoItems = [
                    { label: 'Title Tag', score: breakdown.title_optimisation ?? (seo.page_metadata?.title ? 85 : 0), tip: 'Page title optimization for search engines' },
                    { label: 'Meta Description', score: breakdown.meta_descriptions ?? (seo.page_metadata?.meta_description ? 75 : 0), tip: 'Meta description length and keyword usage' },
                    { label: 'H1 Tags', score: breakdown.heading_structure ?? (seo.page_metadata?.h1_tags?.length ? 80 : 0), tip: 'Heading structure and H1 usage' },
                    { label: 'Content Quality', score: breakdown.content_quality ?? seo.content_analysis?.quality_score ?? 60, tip: 'Word count, readability and depth' },
                    { label: 'Image Alt Text', score: breakdown.image_optimisation ?? (sc?.images_without_alt_count === 0 ? 90 : 50), tip: 'Images with proper alt text' },
                    { label: 'Schema Markup', score: sc?.has_schema_markup ? 90 : 10, tip: 'Structured data for rich snippets' },
                  ]"""

new_breakdown = """                  // Calculate scores based on actual scraped data
                  const title = seo.page_metadata?.title || ''
                  const meta = seo.page_metadata?.meta_description || ''
                  const h1s = seo.page_metadata?.h1_tags || []
                  const imgMissing = sc?.images_without_alt_count || 0
                  const totalImgs = sc?.images_count || 0
                  const wordCount = seo.content_analysis?.word_count || 0

                  const titleScore = (() => {
                    if (!title) return 0
                    if (title.length >= 30 && title.length <= 60) return 95
                    if (title.length >= 20 && title.length <= 70) return 75
                    return 50
                  })()

                  const metaScore = (() => {
                    if (!meta) return 0
                    if (meta.length >= 120 && meta.length <= 160) return 95
                    if (meta.length >= 80 && meta.length <= 180) return 70
                    return 40
                  })()

                  const h1Score = (() => {
                    if (!h1s.length) return 0
                    if (h1s.length === 1) return 95
                    if (h1s.length <= 3) return 70
                    return 50
                  })()

                  const imgScore = (() => {
                    if (totalImgs === 0) return 80
                    const ratio = 1 - (imgMissing / totalImgs)
                    return Math.round(ratio * 100)
                  })()

                  const contentScore = (() => {
                    if (breakdown.content_quality) return breakdown.content_quality
                    if (seo.content_analysis?.quality_score) return seo.content_analysis.quality_score
                    if (wordCount >= 800) return 85
                    if (wordCount >= 400) return 65
                    if (wordCount >= 100) return 45
                    return 20
                  })()

                  const seoItems = [
                    { label: 'Title Tag', score: breakdown.title_optimisation ?? titleScore, tip: \`Title: "\${title.slice(0,40)}..." (\${title.length} chars). Ideal: 30-60 chars\` },
                    { label: 'Meta Description', score: breakdown.meta_descriptions ?? metaScore, tip: \`Meta: \${meta.length} chars. Ideal: 120-160 chars\${!meta ? ' — MISSING' : ''}\` },
                    { label: 'H1 Tags', score: breakdown.heading_structure ?? h1Score, tip: \`Found \${h1s.length} H1 tag\${h1s.length !== 1 ? 's' : ''}. Ideal: exactly 1 H1\${!h1s.length ? ' — MISSING' : ''}\` },
                    { label: 'Content Quality', score: contentScore, tip: \`Word count: \${wordCount}. Ideal: 800+ words for good SEO\` },
                    { label: 'Image Alt Text', score: breakdown.image_optimisation ?? imgScore, tip: \`\${imgMissing} of \${totalImgs} images missing alt text\` },
                    { label: 'Schema Markup', score: sc?.has_schema_markup ? 95 : 0, tip: sc?.has_schema_markup ? 'Schema markup detected ✓' : 'No schema markup found — add Product/Organization schema' },
                  ]"""

content = content.replace(old_breakdown, new_breakdown)

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)

print("Fixed!")
print("Has titleScore:", "titleScore" in content)
print("Has metaScore:", "metaScore" in content)
