# Resume Health Checker - Micro-SaaS

A simple yet effective AI-powered resume analysis tool built for immediate revenue generation with minimal development overhead.

## Architecture Overview

- **Frontend**: Single HTML page with vanilla JavaScript (no frameworks)
- **Backend**: FastAPI (Python) - perfect for serverless deployment  
- **AI**: OpenAI GPT-4o mini (low-cost, high-performance)
- **Payments**: Stripe Payment Links (no-code payment solution)
- **Hosting**: Designed for Vercel/Netlify (serverless functions)
- **Database**: None required - stateless design

## Business Model

- **Free Tier**: Basic resume analysis showing 3 major issues
- **Paid Tier**: $5 detailed report with ATS optimization, metrics, and prioritized recommendations
- **Payment Flow**: Stripe Payment Links → redirect back with token → unlock detailed analysis

## Quick Setup

### Method 1: Automated Setup (Recommended)

**On macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**On Windows or any system:**
```bash
python setup.py setup
```

### Method 2: Manual Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install pre-commit hooks (optional)
pre-commit install
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `STRIPE_PAYMENT_SUCCESS_TOKEN`: Token to validate successful payments (can be any string)

### 3. Local Development

```bash
python main.py
# or
uvicorn main:app --reload
```

Visit `http://localhost:8000` to test the application.

## Deployment Options

### Option 1: Vercel (Recommended)

1. Create `vercel.json`:
```json
{
  "functions": {
    "main.py": {
      "runtime": "python3.9"
    }
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "/main.py"
    }
  ]
}
```

2. Deploy:
```bash
npm i -g vercel
vercel --prod
```

### Option 2: Railway

```bash
railway login
railway init
railway up
```

### Option 3: AWS Lambda (Recommended for Production)

Full AWS deployment with SAM:

```bash
# Install prerequisites
brew install awscli
pip install aws-sam-cli

# Configure AWS
aws configure

# Set environment variables
export OPENAI_API_KEY="your-key"
export STRIPE_PAYMENT_URL="your-url" 
export STRIPE_PAYMENT_SUCCESS_TOKEN="your-token"

# Deploy
./deploy.sh prod
```

See [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md) for detailed instructions.

## Stripe Payment Setup

### 1. Create Stripe Payment Link

1. Go to Stripe Dashboard → Payment Links
2. Create new payment link for $5
3. Set success URL to: `https://yourdomain.com/?payment_token=your_success_token`
4. Update the payment link URL in `main.py` line ~500

### 2. Payment Flow

1. User gets free analysis
2. Clicks "Unlock Full Report - $5" 
3. Redirected to Stripe Payment Link
4. After payment, redirected back with `payment_token` parameter
5. App detects token and provides detailed analysis

## File Processing

Supports:
- **PDF files**: Extracted using PyMuPDF
- **Word documents (.docx)**: Extracted using python-docx

## AI Analysis Types

### Free Analysis
- Overall score (1-100)
- 3 major issues 
- Compelling upgrade message

### Paid Analysis  
- Overall score
- ATS optimization score + recommendations
- Content clarity score + improvements
- Impact metrics score + suggestions
- Formatting score + fixes
- Top 3 prioritized recommendations

## Cost Analysis

### Per Analysis Costs:
- GPT-4o mini: ~$0.01-0.03 per analysis
- Hosting (Vercel): ~$0 (generous free tier)
- Stripe fees: $0.30 + 2.9% = $0.45 per $5 sale

### Profit per sale: ~$4.50 (90% margin)

## Customization

### Modify AI Prompts
Edit the prompt functions in `main.py`:
- `get_free_analysis_prompt()` - Free tier analysis
- `get_paid_analysis_prompt()` - Detailed paid analysis

### Styling
Update the CSS in the HTML template within `main.py` around line ~200.

### Pricing
- Change payment amount in Stripe Payment Link
- Update button text in HTML template

## Security Notes

- File uploads are processed in memory (no persistent storage)
- Environment variables for sensitive keys
- Input validation for file types and sizes
- No user data stored (GDPR friendly)

## Monitoring

Add these endpoints for monitoring:
- `/health` - Health check (already included)
- Add logging for analysis requests
- Monitor OpenAI API usage
- Track conversion rates (free → paid)

## Scaling Considerations

Current setup handles:
- ~1000 requests/month on free tiers
- Serverless auto-scaling
- No database maintenance

For higher volume:
- Add Redis for caching
- Implement rate limiting
- Add user accounts/authentication
- Bulk analysis features

## Testing

Test the application:

1. **Free Analysis**: Upload resume without payment token
2. **Paid Analysis**: Add `?payment_token=payment_success_123` to URL and upload resume
3. **Error Handling**: Try invalid file types, corrupted files

## Support & Maintenance

- Monitor OpenAI API changes
- Update AI prompts based on user feedback  
- A/B test pricing and messaging
- Add new export formats (PDF reports, etc.)

## Revenue Optimization Tips

1. **Improve Conversion**:
   - Make free analysis more compelling
   - Add social proof/testimonials
   - Test different pricing points

2. **Increase Volume**:
   - SEO optimization
   - Content marketing (resume tips blog)
   - Social media integration
   - Referral program

3. **Expand Revenue**:
   - LinkedIn optimization add-on ($3)
   - Cover letter analysis ($3) 
   - Interview prep questions ($5)
   - Resume templates ($10)

This setup gives you a production-ready micro-SaaS that can start generating revenue immediately with minimal ongoing costs.