# Contributing to OSM2terrn

Thank you for considering contributing to **OSM2terrn**! 🎉 This is a community-driven open-source project that generates realistic terrains for **Rigs of Rods** using real-world data from **OpenStreetMap (OSM)** and **OpenTopoData**.

We welcome all contributions, whether it's fixing bugs, improving documentation, or adding new features.

---

## 🛠️ How to Contribute

### 1. Fork the Repository

- Go to [Joako360/osm2terrn](https://github.com/Joako360/osm2terrn).
- Click on **Fork** to create your personal copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/yourusername/osm2terrn.git
cd osm2terrn
```

### 3. Create a Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

- Write clear, modular, and well-documented code.
- Follow the existing project structure and naming conventions.
- For bug fixes, reference the Issue number in your commit message.

### 5. Test Your Code

Ensure your changes work as expected. If possible, provide visual outputs (screenshots, exported files) to validate.

### 6. Commit Your Changes

```bash
git add .
git commit -m "[Feature/Fix]: Clear and concise description of your change"
```

### 7. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 8. Submit a Pull Request

- Go to the **Pull Requests** tab in the original repository.
- Click **New Pull Request** and select your branch.
- Provide a detailed description of your changes, linking any related Issues.
- Check the Pull Request Checklist to ensure everything is in order.

---

## 🧑‍💻 Code Style Guidelines

### General Style

- All code must be **Python 3.10+** compliant.
- Follow **PEP8** coding standards strictly.
- Maintain a balance between readability and optimization (clear code over clever tricks).
- Modularize large code blocks into reusable functions or modules.
- Only use dependencies listed in `requirements.txt`. You may propose a new dependency if justified.

### Naming Conventions

- Variables, functions, methods: `snake_case`
- Classes: `CamelCase`
- Constants: `UPPER_SNAKE_CASE`
- Modules and packages: `snake_case`
- Private methods/variables: Prefix with `_`
- Special methods/attributes: Prefix and suffix with `__`
- Instance methods must have `self` as first argument.
- Class methods must have `cls` as first argument.
- Boolean variables should start with `is_`, `has_`, etc.
- Avoid single-letter variable names (except loop counters).

### Comments & Documentation

- All **public functions must have docstrings** (PEP257 style).
- Write comments in **English**.
- Add explanatory comments for complex code.
- You can use **emojis** in comments or logs if they enhance clarity or context 🎉.

### File Naming

- Use descriptive but concise filenames.
- Avoid generic names like `helpers.py`. Instead, prefer specific names like `heightmap_handler.py`.

### Logging & Error Handling

- Use the existing `logger.py` for logging.
- Add meaningful log messages in important actions, warnings, or potential errors.

---

## 🤖 Copilot Custom Instructions

This project uses **GitHub Copilot Custom Instructions** to guide code suggestions and maintain consistency.

The file `.github/copilot-instructions.md` defines:

- Coding standards and naming conventions.
- Preferred project structure.
- Guidelines for modularity, logging, dependencies, and more.

### How You Can Improve Copilot Instructions:

- If you believe Copilot's suggestions can be improved, you’re encouraged to propose changes.
- Edit `.github/copilot-instructions.md` in a feature branch.
- In your Pull Request, explain why the change is useful and provide an example of how suggestions would improve.
- Keep the instructions concise and aligned with the project’s collaborative philosophy.

---

## 🐞 Reporting Bugs / Requesting Features

- Open an Issue using the provided template.
- Clearly describe the problem or feature request.
- Include reproduction steps (if bug) or use cases (if feature).

---

## 🌟 Community Rules

- Be respectful and constructive in discussions.
- Review Pull Requests and Issues from fellow contributors when possible.
- All contributions are welcome, from beginners to experts.
- We value collaboration and continuous improvement.

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the **GNU GPLv3** license.

---

Thank you for contributing to **OSM2terrn**! 🚀

— Joako360

