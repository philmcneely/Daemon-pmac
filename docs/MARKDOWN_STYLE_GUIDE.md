# Markdown Style Guide for Content Blocks

This guide defines the preferred markdown formatting for all content blocks in the Daemon personal API system. Use this guide when creating or editing content in any endpoint data.

## Header Structure

#### Use H4 (####) as Primary Headers
H4 headers provide the optimal visual hierarchy for content blocks without being too large or too small.

```markdown
#### This is the Preferred Header Level
```

#### Avoid Other Header Levels in Content
- Don't use H1 (#) - Reserved for page titles
- Don't use H2 (##) - Reserved for major sections
- Don't use H3 (###) - Reserved for subsections
- H5 (#####) and H6 (######) are too small for primary content headers

## Text Formatting

#### Emphasis and Strong Text
- Use **bold** for important concepts and key terms
- Use *italics* for emphasis or foreign words
- Use `code` for technical terms, filenames, or inline code
- Use ~~strikethrough~~ for deprecated or removed items

#### Inline Code and Technical Terms
```markdown
Use `backticks` for:
- Variable names: `user_id`
- File names: `config.json`
- Commands: `npm install`
- API endpoints: `/api/v1/data`
```

## List Formatting

#### Standard Bullet Points
Use hyphens (-) for consistent bullet points:

```markdown
- First level item
- Another first level item
- Third item
```

#### Nested Bullet Points (Multiple Techniques)

**Method 1: Four Spaces for Indentation**
```markdown
- Primary item
    - Nested item (4 spaces)
    - Another nested item
        - Deep nested item (8 spaces)
        - Another deep item
- Back to primary level
```

**Method 2: HTML Lists for Complex Nesting**
```markdown
<ul>
<li>Primary item</li>
<li>Another primary item
    <ul>
    <li>Nested item</li>
    <li>Another nested item
        <ul>
        <li>Deep nested item</li>
        <li>Another deep item</li>
        </ul>
    </li>
    </ul>
</li>
<li>Back to primary level</li>
</ul>
```

**Method 3: Non-Breaking Spaces (if converter supports)**
```markdown
- Primary item
-&nbsp;&nbsp;&nbsp;&nbsp;Nested item (4 non-breaking spaces)
-&nbsp;&nbsp;&nbsp;&nbsp;Another nested item
-&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Deep nested item (8 non-breaking spaces)
- Back to primary level
```

#### Numbered Lists
Use standard numbered lists for sequential content:

```markdown
1. First step
2. Second step
3. Third step
```

#### Mixed Lists
Combine numbered and bulleted lists when appropriate:

```markdown
1. Project Setup
    - Install dependencies
    - Configure environment
    - Set up database
2. Development Process
    - Write code
    - Run tests
    - Deploy changes
```

## Code Blocks

#### Fenced Code Blocks
Always specify the language for syntax highlighting:

```markdown
```python
def example_function():
    return "Hello, World!"
```
```

```markdown
```javascript
function exampleFunction() {
    return "Hello, World!";
}
```
```

```markdown
```bash
npm install package-name
```
```

#### Inline vs Block Code
- Use `inline code` for short snippets, commands, or technical terms
- Use fenced code blocks for multi-line code or examples

## Links and References

#### Internal Links
```markdown
See the [API Documentation](API_REQUIREMENTS.md) for details.
```

#### External Links
```markdown
Visit [GitHub](https://github.com) for source code hosting.
```

#### Reference-Style Links
```markdown
Check out [this resource][1] and [that guide][2].

[1]: https://example.com/resource
[2]: https://example.com/guide
```

## Tables

#### Simple Table Format
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Data A   | Data B   | Data C   |
```

#### Aligned Tables
```markdown
| Left Align | Center Align | Right Align |
|:-----------|:------------:|------------:|
| Left       |   Center     |       Right |
| Data       |   More       |        Info |
```

## Quotes and Callouts

#### Blockquotes
```markdown
> This is a blockquote for important information
> that spans multiple lines.
```

#### Code Comments as Callouts
```markdown
<!-- Note: This is important information -->
<!-- TODO: Add more examples -->
<!-- WARNING: This feature is experimental -->
```

## Special Formatting

#### Horizontal Rules
Use three hyphens for section breaks:
```markdown
---
```

#### Line Breaks
- Use two spaces at the end of a line for a soft break
- Use a blank line for paragraph separation

#### Escape Characters
Use backslash to escape special characters:
```markdown
\* This asterisk won't create emphasis
\# This won't be a header
```

## Content Organization Best Practices

#### Structure Your Content
1. Start with an H4 header for the main topic
2. Use bullet points for lists of items or features
3. Use numbered lists for step-by-step processes
4. Include code examples where relevant
5. End with relevant links or references

#### Keep It Scannable
- Use short paragraphs (2-3 sentences max)
- Include plenty of white space
- Use bullet points to break up dense information
- Highlight key terms with **bold** formatting

#### Be Consistent
- Always use the same formatting for similar elements
- Maintain consistent indentation (4 spaces recommended)
- Use the same style for all code blocks
- Keep header hierarchy consistent

## Examples

#### Good Content Block Example
```markdown
#### Python Development Setup

This section covers the essential steps for setting up a Python development environment.

**Prerequisites:**
- Python 3.8 or higher
- Git version control
- Text editor or IDE

**Installation Steps:**
1. Install Python from python.org
2. Set up virtual environment:
    ```bash
    python -m venv project_env
    source project_env/bin/activate  # On Windows: project_env\Scripts\activate
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

**Key Configuration Files:**
- `requirements.txt` - Python dependencies
- `.env` - Environment variables
- `config.py` - Application configuration

**Useful Resources:**
- [Python Documentation](https://docs.python.org/)
- [Virtual Environments Guide](https://docs.python.org/3/tutorial/venv.html)

---

#### Next: Configure your development tools
```

#### Poor Content Block Example (Avoid)
```markdown
# PYTHON SETUP (wrong header level)

python development setup information

Prerequisites:
python 3.8
git
editor

1. install python
2. make virtual environment: python -m venv project_env
3. activate it
4. install stuff: pip install -r requirements.txt

files:
requirements.txt
.env
config.py

see python docs for more info
```

## Markdown Converter Compatibility

#### Safe Formatting for All Converters
- Use standard markdown syntax
- Avoid HTML when possible
- Test complex nesting with your specific converter
- Fall back to simpler formatting if advanced features don't work

#### HTML Fallbacks
If your markdown converter doesn't support advanced features:
- Use `<br>` for forced line breaks
- Use `<ul>` and `<li>` for complex nested lists
- Use `<strong>` and `<em>` for emphasis
- Use `<code>` for inline code

Remember: **Consistency and readability are more important than complex formatting.** Choose the approach that works best with your markdown converter and stick with it throughout your content.
