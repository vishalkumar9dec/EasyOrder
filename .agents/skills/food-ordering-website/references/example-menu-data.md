# Example Menu Data & Image Prompts

## Vietnamese Cuisine Example

### Menu Items

```javascript
export const menuData = {
  categories: ["Starters", "Pho & Noodles", "Rice Dishes", "Desserts", "Drinks"],
  items: [
    {
      id: 1,
      name: "Gỏi Cuốn",
      description: "Fresh spring rolls with shrimp, herbs, and peanut dipping sauce",
      price: 8.50,
      category: "Starters",
      image: "/images/goi-cuon.jpg",
      badge: null
    },
    {
      id: 2,
      name: "Phở Bò",
      description: "24-hour beef bone broth with rice noodles, rare sirloin, and herbs",
      price: 14.00,
      category: "Pho & Noodles",
      image: "/images/pho-bo.jpg",
      badge: "Popular"
    },
    {
      id: 3,
      name: "Bún Chả Hà Nội",
      description: "Grilled pork patties with vermicelli, pickled vegetables, and nuoc cham",
      price: 15.50,
      category: "Pho & Noodles",
      image: "/images/bun-cha.jpg",
      badge: null
    },
    {
      id: 4,
      name: "Cơm Tấm",
      description: "Broken rice with grilled lemongrass pork chop, fried egg, and pickles",
      price: 13.00,
      category: "Rice Dishes",
      image: "/images/com-tam.jpg",
      badge: "Chef's Pick"
    },
    {
      id: 5,
      name: "Bánh Xèo",
      description: "Crispy turmeric crepe filled with shrimp, pork, and bean sprouts",
      price: 12.00,
      category: "Starters",
      image: "/images/banh-xeo.jpg",
      badge: null
    },
    {
      id: 6,
      name: "Chè Ba Màu",
      description: "Three-color dessert with mung bean, red bean, and pandan jelly",
      price: 7.00,
      category: "Desserts",
      image: "/images/che-ba-mau.jpg",
      badge: null
    },
    {
      id: 7,
      name: "Cà Phê Sữa Đá",
      description: "Vietnamese iced coffee with sweetened condensed milk",
      price: 5.50,
      category: "Drinks",
      image: "/images/ca-phe-sua-da.jpg",
      badge: "Signature"
    },
    {
      id: 8,
      name: "Mì Quang",
      description: "Turmeric noodles with shrimp, pork, herbs, and crispy rice crackers",
      price: 14.50,
      category: "Pho & Noodles",
      image: "/images/mi-quang.jpg",
      badge: null
    }
  ]
};
```

### Image Prompts for Vietnamese Cuisine

**Hero:**
```
Overhead shot of a Vietnamese feast on a dark wooden table — pho, spring rolls, 
banh mi, and herbs scattered artfully. Warm dramatic side lighting, steam rising 
from the pho bowl, rich colors, food photography style, shallow depth of field, 
no text or UI elements
```

**Dish images:**
```
1. "Fresh Vietnamese spring rolls (goi cuon) on dark slate plate, dipping sauce 
    in small bowl beside them, dramatic warm lighting, food photography, no text"

2. "Steaming bowl of Vietnamese pho with rare beef slices, fresh herbs, bean 
    sprouts, and lime wedges on dark surface, overhead shot, warm lighting, no text"

3. "Vietnamese bun cha — grilled pork patties with vermicelli noodles and fresh 
    herbs in separate bowls on dark wood table, food magazine style, no text"

4. "Vietnamese broken rice (com tam) plate with grilled pork chop, fried egg, 
    and pickled vegetables on dark background, warm side lighting, no text"

5. "Golden crispy Vietnamese banh xeo crepe on dark plate, filled with shrimp 
    and bean sprouts, dramatic lighting, food photography, no text"

6. "Vietnamese three-color dessert (che ba mau) in a clear glass, showing 
    colorful layers, on dark marble surface, soft warm lighting, no text"

7. "Vietnamese iced coffee (ca phe sua da) in a tall glass with condensed milk 
    swirling, dark moody background, dramatic lighting, food photography, no text"

8. "Bowl of Vietnamese mi quang turmeric noodles with shrimp and herbs, topped 
    with crispy rice crackers, dark background, warm lighting, no text"
```

**Featured/Spotlight:**
```
1. "Close-up dramatic shot of Vietnamese pho bo — beef bone broth with tender 
    slices of rare sirloin, steam rising, fresh Thai basil and lime, rich warm 
    tones, dark moody background, professional food photography, no text"

2. "Artful arrangement of Vietnamese spring rolls cut in half showing the fresh 
    shrimp and herb filling, peanut sauce drizzle, on dark slate, dramatic 
    macro food photography, no text"
```

## Indian Cuisine Example (alternate palette)

For Indian cuisine, shift the palette warmer:
- `--accent`: `#E85D2C` (tandoori red-orange)
- `--accent-gold`: `#F5C842` (turmeric gold)
- Typography: consider "Cormorant Garamond" for display

## Japanese Cuisine Example (alternate palette)

For Japanese cuisine, shift the palette cooler and more minimal:
- `--accent`: `#C53030` (vermillion red)
- `--accent-gold`: `#D4A373` (warm beige)
- `--surface`: `#141414`
- Typography: consider "DM Serif Display" for display
- Reduce border-radius to 8px for a more angular, precise feel
