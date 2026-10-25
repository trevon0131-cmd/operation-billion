"""Twenty-nine different, locally generative business-specialist workers."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Bot:
    key: str
    name: str
    lane: str
    artifact: str
    audience: str
    subject: str
    pitch: str
    suggested_price: float
    channel: str
    cost_to_draft: float = 0.0
    notes: str = ''

# A recommended price is never an asserted market price or guaranteed income.
BOTS = [
    Bot('sticker_studio', 'Sticker Studio', 'Digital artwork', 'svg', 'students', 'Keep Growing', 'An original botanical sticker design delivered as a downloadable SVG and PNG', 3.00, 'Ko-fi / Gumroad'),
    Bot('wall_art', 'Wall Art Atelier', 'Printable decor', 'svg', 'home office owners', 'Progress Over Perfection', 'Minimalist typography wall art for home printing', 4.00, 'Ko-fi / Gumroad'),
    Bot('icon_pack', 'Icon Workshop', 'Design assets', 'svg', 'website makers', 'Simple Shapes', 'Editable geometric icon and pattern starter', 3.00, 'Ko-fi / Gumroad'),
    Bot('gift_tags', 'Gift Tag Maker', 'Printables', 'svg', 'gift givers', 'Made With Care', 'Print-at-home geometric gift tag design', 2.00, 'Ko-fi / Gumroad'),
    Bot('greeting_cards', 'Greeting Card Studio', 'Cards', 'svg', 'family and friends', 'You Got This', 'Printable encouragement card with original abstract layout', 3.00, 'Ko-fi / Gumroad'),
    Bot('pattern_designer', 'Pattern Lab', 'Design assets', 'svg', 'craft hobbyists', 'Shape Garden', 'Repeating decorative pattern for personal crafts', 3.00, 'Ko-fi / Gumroad'),
    Bot('coloring_pages', 'Coloring Page Artist', 'Printables', 'svg', 'families', 'Creative Day', 'Line-art geometric coloring page for printing', 2.00, 'Ko-fi / Gumroad'),
    Bot('classroom_posters', 'Classroom Poster Maker', 'Classroom assets', 'svg', 'teachers', 'Ask Great Questions', 'Original classroom motivation poster', 3.00, 'Ko-fi / Gumroad'),
    Bot('local_service_flyer', 'Local Flyer Designer', 'Services', 'svg', 'local small businesses', 'Grow Locally', 'Customizable marketing flyer draft for local services', 10.00, 'Freelance delivery'),
    Bot('digital_invitations', 'Invitation Designer', 'Event assets', 'svg', 'event planners', 'Celebrate Together', 'Editable invitation card template', 3.00, 'Ko-fi / Gumroad'),
    Bot('budget_planner', 'Budget Planner Builder', 'Spreadsheets', 'csv', 'budget beginners', 'Monthly Budget Tracker', 'Reusable budget table with prebuilt categories', 4.00, 'Ko-fi / Gumroad'),
    Bot('inventory_tracker', 'Inventory Sheet Builder', 'Business spreadsheets', 'csv', 'small resellers', 'Inventory Basics', 'Editable inventory and margin sheet', 4.00, 'Ko-fi / Gumroad'),
    Bot('price_calculator', 'Pricing Tool Builder', 'Business utilities', 'html', 'digital product sellers', 'Pricing Calculator', 'Offline, single-page pricing calculator', 5.00, 'Ko-fi / Gumroad'),
    Bot('study_planner', 'Study Planner Lab', 'Student tools', 'html', 'college students', 'Weekly Study Planner', 'Printable weekly study schedule template', 3.00, 'Ko-fi / Gumroad'),
    Bot('habit_tracker', 'Habit Tracker Lab', 'Wellness printables', 'html', 'habit builders', 'Habit Tracking Sheet', 'Simple 30-day printable habit tracker', 3.00, 'Ko-fi / Gumroad'),
    Bot('meal_planner', 'Meal Planner Lab', 'Home printables', 'html', 'busy households', 'Weekly Meal Plan', 'Printable menu and grocery checklist', 3.00, 'Ko-fi / Gumroad'),
    Bot('cleaning_checklist', 'Cleaning System Maker', 'Home printables', 'html', 'busy households', 'Weekly Home Reset', 'Room-by-room printable checklist', 2.00, 'Ko-fi / Gumroad'),
    Bot('resume_template', 'Resume Layout Studio', 'Career templates', 'html', 'job seekers', 'Clean Resume Template', 'Original one-page resume layout, ready to customize', 5.00, 'Ko-fi / Gumroad'),
    Bot('learning_worksheets', 'Worksheet Creator', 'Educational products', 'html', 'tutors', 'Practice Sheet', 'Editable blank practice sheet for original teaching materials', 3.00, 'Ko-fi / Gumroad'),
    Bot('landing_page_kit', 'Landing Page Builder', 'Web design services', 'html', 'new businesses', 'Simple Launch Page', 'Customizable no-framework landing page template', 15.00, 'Freelance delivery'),
    Bot('social_caption_pack', 'Caption Copywriter', 'Content packs', 'md', 'small creators', 'Content Ideas for Makers', 'Original social post prompts and caption examples', 4.00, 'Ko-fi / Gumroad'),
    Bot('blog_outline', 'Blog Research Planner', 'Writing services', 'md', 'independent creators', 'Helpful Article Outlines', 'Original non-factual topic outlines for client customization', 6.00, 'Freelance delivery'),
    Bot('newsletter_kit', 'Newsletter Pack Builder', 'Newsletter services', 'md', 'newsletter writers', 'Monthly Newsletter Kit', 'A newsletter structure, editorial calendar and CTA options', 5.00, 'Freelance delivery'),
    Bot('interview_prep', 'Interview Prep Writer', 'Career products', 'md', 'new job seekers', 'Interview Questions Practice', 'Printable questions and reflection prompts, no invented answers', 4.00, 'Ko-fi / Gumroad'),
    Bot('cover_letter', 'Cover Letter Framework', 'Career products', 'md', 'job seekers', 'Cover Letter Starter', 'Original fill-in-the-blank cover letter guide', 3.00, 'Ko-fi / Gumroad'),
    Bot('website_pitch', 'Website Proposal Writer', 'Freelance services', 'md', 'freelance web designers', 'Website Proposal Template', 'Honest, editable prospective client proposal, not an unsolicited message', 4.00, 'Freelance delivery'),
    Bot('micro_saas', 'Micro-SaaS Scout', 'Software products', 'md', 'indie developers', 'Small Utility App Concept', 'Testable software concept and no-spend validation plan', 0.00, 'Research only', notes='An idea is not an income source until built and sold'),
    Bot('affiliate_review', 'Affiliate Research Desk', 'Affiliate publishing', 'md', 'niche bloggers', 'Transparent Comparison Outline', 'Disclosure-first article outline without fabricated comparisons', 0.00, 'Research only', notes='Requires an approved affiliate program and genuine product evidence before publishing'),
    Bot('ebay_sticker_scout', 'eBay Sticker Scout', 'Physical ecommerce research', 'md', 'sticker sellers', 'Physical Sticker Listing Plan', 'A research-only checklist for physical stickers, including production, stock and shipping', 0.00, 'Research only', notes='Physical fulfillment is not free; no physical listings without fulfillment and inventory proof'),
]

BY_KEY = {bot.key: bot for bot in BOTS}
