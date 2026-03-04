# Course details (per-course folder)

This folder holds **one folder per course** so the chatbot can load only the relevant course when answering. **Every answer must include the `source_url`** of the course the information came from.

## Structure

```
course_details/
  index.json          # Maps course key → source_url, path, course_name (use for returning URL in answers)
  product_management/
    course.json       # Full Product Manager Fellowship data
  ux_design/
    course.json       # Full UI/UX Designer Fellowship data
  data_analytics/
    course.json       # Full Data Analyst Fellowship data
  business_analytics/
    course.json       # Full Business Analyst Fellowship data
  genai_bootcamp/
    course.json       # Full Applied Generative AI Bootcamp data
```

## Data source

- Each `course.json` is a **copy of the updated reference data** from `data/reference/<course>.json`.
- When reference data is updated (e.g. after you feed new data), re-copy into this folder or run the sync script so `course_details` stays in sync.

## Returning the correct URL

- **index.json** has for each course: `source_url`, `course_name`, `path`.
- When the user asks about a course (e.g. "What is the fee for Product Manager Fellowship?"):
  1. Load the relevant course from `course_details/<key>/course.json` (or use index to find path).
  2. Answer using that course’s data.
  3. **Always include in the response:** “Source: <source_url>” (from `index.json` for that course).

Example: For Product Manager questions, return  
`Source: https://nextleap.app/course/product-management-course`

## Course keys

| Key                | Course name                     | source_url |
|--------------------|----------------------------------|------------|
| product_management | Product Manager Fellowship      | https://nextleap.app/course/product-management-course |
| ux_design          | UI/UX Designer Fellowship       | https://nextleap.app/course/ui-ux-design-course |
| data_analytics     | Data Analyst Fellowship         | https://nextleap.app/course/data-analyst-course |
| business_analytics | Business Analyst Fellowship     | https://nextleap.app/course/business-analyst-course |
| genai_bootcamp     | Applied Generative AI Bootcamp  | https://nextleap.app/course/generative-ai-course |
