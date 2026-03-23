# Search Audit Impact Map (SAIM)

Reference data for linking audit findings to industry statistics and Algolia customer success stories.

## No Typo Tolerance
- **Stat**: 1 in 6 search queries contain a typo. Without typo tolerance, those searches return zero results.
- **Case Study**: Lacoste saw a 37% increase in search revenue after implementing Algolia's typo tolerance.

## Slow Search / High Latency
- **Stat**: 39% of shoppers will leave a site if search is too slow. Every 100ms delay costs 1% in revenue.
- **Case Study**: Under Armour reduced search latency to under 20ms with Algolia, improving engagement.

## No Federated Search
- **Stat**: 68% of shoppers say they would return to a site with a good search experience. Federated search surfaces products, content, and categories together.
- **Case Study**: Staples implemented federated search and saw improved content discoverability alongside product results.

## No Personalization
- **Stat**: 80% of consumers are more likely to buy from a brand that offers personalized experiences. Personalization can lift revenue by 10-15%.
- **Case Study**: Gymshark used Algolia personalization to increase conversion rate by tailoring results to individual user behavior.

## Poor Relevance
- **Stat**: 72% of sites have "mediocre" or "broken" search relevance (Bayard Institute). Poor relevance is the #1 reason users abandon search.
- **Case Study**: Decathlon improved search relevance with Algolia's custom ranking, boosting search conversion by 50%.

## No Filters / Bad Filters
- **Stat**: 43% of sites don't offer sufficient product filtering. Users who use filters convert at 2x the rate of those who don't.
- **Case Study**: Birkenstock implemented dynamic faceting with Algolia to surface category-relevant filters automatically.

## Missing Sort Options (Need 4 minimum)
- **Stat**: Users expect at minimum: Relevance, Price Low-High, Price High-Low, and Newest/Best Rated. 46% of sites are missing at least one key sort option.
- **Case Study**: Multiple Algolia customers implement Sort By Replicas for fast, pre-computed sort orders.

## Browse & Search Inconsistency
- **Stat**: When search and browse/navigation show different results for the same products, it erodes user trust and creates confusion.
- **Case Study**: Algolia unifies search and browse under one index with merchandising rules applied consistently.

## No Results Pages
- **Stat**: 12% of searches lead to no-results pages. 75% of users who hit a no-results page leave the site entirely.
- **Case Study**: Herschel Supply reduced no-results rate by 80% with Algolia's synonym management and query suggestions.

## Out of Stock Items at Top
- **Stat**: Showing out-of-stock products at the top of results wastes valuable real estate and frustrates users.
- **Case Study**: Algolia's custom ranking allows boosting in-stock items and demoting out-of-stock via business metrics.

## Not Showing Proper Variants
- **Stat**: When color/size variants aren't properly grouped, the same product appears multiple times, cluttering results.
- **Case Study**: Algolia's distinct feature groups product variants so each product appears once with variant selectors.

## No Banners / Merchandising
- **Stat**: Banners in search results can drive campaign visibility. Sites without merchandising miss promotional opportunities.
- **Case Study**: Algolia Rules engine allows injecting banners, redirects, and promoted content based on query context.

## Blank Empty State Search
- **Stat**: The empty search state (when user clicks search before typing) is a prime merchandising opportunity. Most sites show nothing.
- **Case Study**: Best practice is to show trending searches, popular products, or personalized suggestions in the empty state.

## Irrelevant Recommendations
- **Stat**: Product recommendations drive 31% of e-commerce revenue. Irrelevant recommendations are worse than no recommendations.
- **Case Study**: Algolia Recommend uses ML models (Frequently Bought Together, Related Products, Trending) trained on user events.

## Not Factoring Product Reviews
- **Stat**: 93% of consumers say reviews influence their purchase decision. Search results that don't factor review scores miss a relevance signal.
- **Case Study**: Algolia custom ranking can incorporate average rating and review count into the ranking formula.
