# ☕ The Daily Drip

A mobile-first React + Tailwind CSS prototype for a personalized coffee brewing recipe app.

## Features

### 1. **User Profile**
- Display user information and coffee preferences
- Show brewing statistics
- Customizable preferences (brew strength, flavor notes, methods, temperature, grind size)

### 2. **Bean Collection**
- View and manage coffee bean collection
- Add, edit, and delete beans (mock interactions)
- Display origin, roast level, flavor notes, and purchase info
- Mark favorite beans

### 3. **Recipe Generator**
- Generate personalized brewing recipes based on text prompts
- Visual step-by-step brewing diagram with icons
- Detailed ingredient specifications
- Time-based brewing instructions

## Tech Stack

- **React** 18.2.0
- **Tailwind CSS** 3.3.2
- **Lucide React** (for icons)
- **React Scripts** 5.0.1

## Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Usage

### Viewing in Mobile Mode

For the best experience, view the app in mobile viewport:

1. Open Chrome DevTools (F12 or Cmd+Option+I)
2. Click the device toolbar icon (Cmd+Shift+M)
3. Select a mobile device (e.g., iPhone 12 Pro, Pixel 5) or set custom dimensions (375-430px width)

### Navigation

Use the bottom navigation bar to switch between:
- **Profile**: View user info and preferences
- **Beans**: Manage coffee bean collection
- **Recipe**: Generate brewing recipes

### Try the Recipe Generator

Example prompts:
- "Help me design a recipe for a sunny Sunday morning"
- "I want a strong coffee to start my day"
- "Something light and refreshing"

## Project Structure

```
the-daily-drip/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Profile.js          # User profile component
│   │   ├── BeanCollection.js   # Bean management component
│   │   └── RecipeGenerator.js  # Recipe generation component
│   ├── App.js                   # Main app with navigation
│   ├── index.js                 # Entry point
│   └── index.css                # Global styles with Tailwind
├── package.json
├── tailwind.config.js
└── README.md
```

## Design Notes

- **Mobile-First**: Optimized for 375-430px width viewports
- **Color Scheme**: Custom coffee-themed color palette
- **Mock Data**: All data is hardcoded; no backend required
- **Interactions**: Add/edit/delete actions show alerts or modals (mock functionality)

## Customization

### Colors

The app uses a custom coffee color palette defined in `tailwind.config.js`:
- `coffee-50` to `coffee-900` for various shades

### Mock Data

To modify the mock data:
- **Profile**: Edit the `userProfile` object in `src/components/Profile.js`
- **Beans**: Edit the `beans` state in `src/components/BeanCollection.js`
- **Recipes**: Edit the `mockRecipes` object in `src/components/RecipeGenerator.js`

## Future Enhancements

- Backend integration for data persistence
- Real recipe generation using AI/ML
- User authentication
- Recipe sharing and community features
- Brewing timer functionality
- Coffee journal and tasting notes

## License

This is a prototype project for educational purposes.
