# N-of-1 Platform - React Frontend

Modern React frontend for the N-of-1 Enhanced Reverse Search Platform.

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- npm or yarn
- Backend API running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The app will open at `http://localhost:3000`

### Backend API

Make sure the FastAPI backend is running:
```bash
cd ..
source venv/bin/activate
uvicorn app:app --reload
```

## 📁 Project Structure

```
frontend/
├── public/                 # Static files
├── src/
│   ├── components/        # React components
│   │   ├── Dashboard.tsx          # Main pipeline analysis
│   │   ├── SolicitationForm.tsx   # Input form
│   │   ├── ResultsDisplay.tsx     # Results with SWOT
│   │   ├── ScoreVisualization.tsx # Score charts
│   │   └── CompanyManager.tsx     # Company CRUD
│   ├── services/
│   │   └── api.ts         # API service layer
│   ├── App.tsx            # Main app component
│   ├── index.tsx          # Entry point
│   └── index.css          # Tailwind styles
├── package.json
└── tailwind.config.js
```

## 🎨 Features

### Pipeline Analysis
- Interactive solicitation form
- Real-time pipeline execution
- 6-module workflow visualization
- Comprehensive results display

### Results Display
- Company ranking with validation levels
- SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
- Risk assessment
- Score breakdowns
- Recommended actions
- Decision rationale

### Company Management
- Add/view companies
- Seed sample data
- Search and filter
- Company profiles

### Visualizations
- Score breakdown charts
- Progress bars for each module
- Color-coded validation levels
- Risk level indicators

## 🛠️ Technologies

- **React 19** with TypeScript
- **Tailwind CSS** for styling
- **Axios** for API calls
- **Recharts** for visualizations
- **Create React App** build system

## 📊 API Integration

The frontend connects to the FastAPI backend via:
- Development: `http://localhost:8000` (proxied)
- Production: Configure `REACT_APP_API_URL` environment variable

### API Endpoints Used

- `POST /api/full-pipeline` - Main analysis endpoint
- `POST /api/match` - Basic matching
- `GET /api/companies/search` - List companies
- `POST /api/companies` - Create company
- `POST /seed` - Seed sample data

## 🎯 Usage

### 1. Run Pipeline Analysis

1. Click "Pipeline Analysis" tab
2. Fill in solicitation details:
   - Title and agency
   - NAICS codes
   - Set-asides and clearances
   - Required capabilities
   - Keywords
3. Toggle enrichment (on for full analysis)
4. Set number of companies to analyze
5. Click "Run Full Pipeline Analysis"

### 2. View Results

- See ranked companies
- Click company for detailed view
- Review scores, SWOT, risks
- Follow recommended actions

### 3. Manage Companies

1. Click "Companies" tab
2. Add new companies or seed sample data
3. View company profiles
4. Use companies in analysis

## 🚢 Deployment

### Build for Production

```bash
npm run build
```

Creates optimized build in `build/` folder.

### Environment Variables

Create `.env.production`:
```
REACT_APP_API_URL=https://your-api-domain.com
```

### Deploy Options

- **Static Hosting**: Netlify, Vercel, S3
- **Docker**: Include in container
- **Nginx**: Serve static files

Example Nginx config:
```nginx
server {
    listen 80;
    root /var/www/frontend/build;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## 🎨 Customization

### Colors

Edit `tailwind.config.js`:
```javascript
theme: {
  extend: {
    colors: {
      primary: {...}
    }
  }
}
```

### API URL

Edit `.env`:
```
REACT_APP_API_URL=http://your-api-url
```

## 📝 Available Scripts

- `npm start` - Development server (port 3000)
- `npm run build` - Production build
- `npm test` - Run tests
- `npm run eject` - Eject from CRA (irreversible)

## 🐛 Troubleshooting

### API Connection Issues

**Problem**: "Network Error" or "CORS error"

**Solution**:
1. Verify backend is running on port 8000
2. Check proxy in `package.json`
3. Ensure CORS is enabled in FastAPI

### Styling Issues

**Problem**: Tailwind styles not loading

**Solution**:
1. Verify `tailwind.config.js` exists
2. Check `import './index.css'` in `index.tsx`
3. Restart dev server

### Build Errors

**Problem**: TypeScript errors

**Solution**:
```bash
npm install --save-dev @types/node @types/react @types/react-dom
```

## 📚 Learn More

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Create React App](https://create-react-app.dev/)

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit for review

---

**Version**: 1.0  
**Last Updated**: October 2025
