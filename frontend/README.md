# DTO Frontend

Next.js 14 frontend for the Data Testing Orchestrator.

## Architecture

```
app/
├── globals.css          # Global styles and CSS variables
├── layout.tsx           # Root layout with providers
├── page.tsx            # Home page
├── runs/               # Test run pages
├── datasets/           # Dataset browser pages
├── builder/            # Test builder pages
└── settings/           # Settings pages

components/
├── ui/                 # shadcn/ui components
│   ├── button.tsx
│   ├── card.tsx
│   ├── badge.tsx
│   └── ...
├── navigation.tsx      # Main navigation
├── theme-provider.tsx  # Theme context
├── query-provider.tsx  # React Query setup
├── runs-table.tsx      # Run history table
└── stats-cards.tsx     # Dashboard stats

lib/
├── api-client.ts       # API client with TypeScript types
└── utils.ts           # Utility functions

hooks/
└── use-toast.ts       # Toast notifications
```

## Development

### Setup
```bash
cd frontend
npm install
```

### Running
```bash
# Development server
npm run dev

# Production build
npm run build
npm start
```

### Code Quality
```bash
# Linting
npm run lint

# Type checking
npm run type-check
```

## Features

### Pages
- **Home**: Dashboard with recent runs and quick actions
- **Test Builder**: Zero-SQL test creation with dynamic cards
- **Runs**: Test execution history and results
- **Datasets**: Catalog browser with schema information
- **Settings**: Configuration for connections, policies, and AI

### Components
- **Responsive Design**: Mobile-first with Tailwind CSS
- **Dark Mode**: System preference with manual toggle
- **Real-time Updates**: React Query for server state
- **Accessibility**: ARIA labels and keyboard navigation
- **Type Safety**: Full TypeScript coverage

### State Management
- **Server State**: TanStack Query for API data
- **Client State**: Zustand for UI state
- **Form State**: React Hook Form with Zod validation

## Configuration

Environment variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL

## Styling

The frontend uses:
- **TailwindCSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality React components
- **CSS Variables**: Theme-aware color system
- **Dark Mode**: Automatic system detection

## API Integration

The frontend communicates with the backend via a typed API client:

```typescript
import { apiClient } from '@/lib/api-client'

// List test runs
const runs = await apiClient.listRuns({ limit: 10 })

// Compile a test
const result = await apiClient.compileTest({
  expression: "order total should be positive",
  dataset: "PREP.ORDERS"
})
```
