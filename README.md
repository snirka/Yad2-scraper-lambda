# Yad2 Car Scraper 🚗

A Python-based car listing scraper for Yad2.co.il that monitors for new car listings based on your custom filters and sends notifications via Telegram.

## Features ✨

- **Custom Search Filters**: Set up multiple search filters with specific criteria (manufacturer, model, year, km, price, etc.)
- **Telegram Notifications**: Get instant notifications when new listings match your filters
- **Automatic Scheduling**: Runs every 15 minutes to check for new listings
- **Change Detection**: Only notifies about truly new listings
- **Manufacturer/Model Mapping**: Human-readable names for car manufacturers and models
- **Comprehensive Logging**: Track all scraping activity and errors
- **Easy Configuration**: Simple setup and filter management

## Installation 🛠️

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd projectX
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Telegram bot** (easiest way)
   ```bash
   python setup_telegram.py
   ```
   
   Or manually:
   - Create a bot via @BotFather on Telegram
   - Get your bot token and chat ID
   - Set environment variables:
     ```bash
     export TELEGRAM_BOT_TOKEN="your_bot_token"
     export TELEGRAM_CHAT_ID="your_chat_id"
     ```

## Deployment Options 🚀

### Option 1: Local Deployment (Traditional)

## Quick Start 🚀

1. **Test Telegram connection**
   ```bash
   python main.py test-telegram
   ```

2. **Run a single scrape to test**
   ```bash
   python main.py scrape-once
   ```

3. **Start the scheduler** (runs every 15 minutes)
   ```bash
   python main.py run
   ```

### Option 2: AWS Lambda Deployment (Serverless) ☁️

Deploy the scraper as a serverless AWS Lambda function that runs automatically every 15 minutes.

#### Prerequisites
- AWS CLI configured with appropriate credentials
- Telegram bot token and chat ID
- (Optional) Terraform for infrastructure-as-code

#### Quick Lambda Deployment

1. **Using the deployment script** (recommended):
   ```bash
   # Set your Telegram credentials
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   
   # Deploy to AWS
   ./deploy_lambda.sh
   ```

2. **Using Terraform** (for production):
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   
   terraform init
   terraform plan
   terraform apply
   ```

#### Environment Variable Configuration

Configure your filters using environment variables with **automatic name-to-ID translation**:

**Method 1: JSON Format with Names**
```bash
aws lambda update-function-configuration --function-name yad2-car-scraper --environment Variables='{
  "TELEGRAM_BOT_TOKEN":"your_token",
  "TELEGRAM_CHAT_ID":"your_chat_id",
  "FILTER_1":"{\"name\":\"audi-a3\",\"manufacturer\":\"אאודי\",\"model\":\"A3\",\"year\":\"2020-2023\"}",
  "FILTER_2":"{\"name\":\"seat-ibiza\",\"manufacturer\":\"Seat\",\"model\":\"איביזה\",\"year\":\"2015-2020\"}"
}'
```

**Method 2: Individual Variables with Names**
```bash
aws lambda update-function-configuration --function-name yad2-car-scraper --environment Variables='{
  "TELEGRAM_BOT_TOKEN":"your_token",
  "TELEGRAM_CHAT_ID":"your_chat_id",
  "FILTER_1_NAME":"my-audi-filter",
  "FILTER_1_MANUFACTURER":"אאודי",
  "FILTER_1_MODEL":"A3",
  "FILTER_1_YEAR":"2020-2023",
  "FILTER_1_KM":"1-50000"
}'
```

**Method 3: Single Filter (Backwards Compatible)**
```bash
aws lambda update-function-configuration --function-name yad2-car-scraper --environment Variables='{
  "TELEGRAM_BOT_TOKEN":"your_token",
  "TELEGRAM_CHAT_ID":"your_chat_id",
  "MANUFACTURER":"אאודי",
  "MODEL":"A3",
  "YEAR":"2020-2023"
}'
```

#### Lambda Benefits
- **No server maintenance**: AWS manages everything
- **Cost-effective**: Pay only for execution time (~$0.70/month)
- **Automatic scaling**: No capacity planning needed
- **High availability**: Built-in redundancy
- **Monitoring**: CloudWatch logs and metrics included
- **Name translation**: Use car names instead of numeric IDs
- **S3 storage**: Persistent data storage without local file system
- **Serverless design**: Fully read-only Lambda environment

#### Monitoring Lambda
```bash
# View logs
aws logs tail /aws/lambda/yad2-car-scraper --follow

# Test function
aws lambda invoke --function-name yad2-car-scraper --payload '{}' response.json
```

📖 **See `terraform/README.md` for detailed Lambda deployment instructions.**

## Configuration 📝

### Adding Search Filters

Create custom search filters interactively:
```bash
python main.py add-filter
```

Example filter for Seat Ibiza 2012-2015 with low kilometers:
- **Name**: "Seat Ibiza 2012-2015 Low KM"
- **Manufacturer ID**: 37 (Seat)
- **Model ID**: 10507 (Ibiza)  
- **Year**: 2012-2015
- **Kilometers**: -1-89000

### Filter Parameters

Based on the Yad2 URL structure, you can filter by:

- **manufacturer**: Manufacturer ID (e.g., 37 for Seat)
- **model**: Model ID (e.g., 10507 for Ibiza)
- **year**: Year range (e.g., "2012-2015")
- **km**: Kilometer range (e.g., "-1-89000" for up to 89,000 km)
- **price**: Price range (e.g., "50000-150000")
- **hand**: Hand number (e.g., "1" for first hand)
- **engine_size**: Engine size range
- **gear**: Transmission type
- **color**: Color code
- **area**: Geographic area code

### Finding Manufacturer and Model IDs

The scraper includes tools to help you find the correct IDs:

```bash
# List all known manufacturers
python main.py list-manufacturers

# List models for a specific manufacturer
python main.py list-models --manufacturer-id 37

# Search for manufacturers by name
# (use the interactive filter creator for easier searching)
python main.py add-filter
```

### Manufacturer and Model IDs (REAL DATA!)

✅ **Updated with real Yad2 API data** - 121 manufacturers mapped!

**Key Manufacturer IDs:**
- **37**: סיאט (Seat) 
- **32**: ניסאן (Nissan)
- **19**: טויוטה (Toyota)
- **41**: פולקסווגן (Volkswagen)  
- **31**: מרצדס-בנץ (Mercedes-Benz)
- **7**: ב מ וו (BMW)
- **1**: אאודי (Audi)
- **40**: סקודה (Skoda)
- **27**: מאזדה (Mazda)
- **17**: הונדה (Honda)
- **43**: פורד (Ford)
- **48**: קיה (Kia)
- **21**: יונדאי (Hyundai)
- **51**: רנו (Renault)
- **46**: פיג'ו (Peugeot)
- **38**: סיטרואן (Citroen)

**To see all manufacturers:**
```bash
python main.py list-manufacturers
```

**To see models for a manufacturer:**
```bash
python main.py list-models --manufacturer-id 37  # Seat models
```

## Usage Commands 💻

```bash
# Start the scraper (default - runs every 15 minutes)
python main.py run

# Run a single scrape cycle
python main.py scrape-once

# Filter management
python main.py add-filter              # Add new filter interactively
python main.py list-filters            # Show all configured filters  
python main.py remove-filter --filter-name "Filter Name"

# Manufacturer/Model lookup
python main.py list-manufacturers      # Show all manufacturers
python main.py list-models --manufacturer-id 37

# Testing
python main.py test-telegram          # Test Telegram connection
```

## Scheduling Options ⏰

### Option 1: Built-in Scheduler (Recommended)
The scraper has a built-in scheduler that runs every 15 minutes:
```bash
python main.py run
```

### Option 2: Cron (Linux/macOS)
Add to your crontab for system-level scheduling:
```bash
# Edit crontab
crontab -e

# Add this line to run every 15 minutes
*/15 * * * * cd /path/to/projectX && python main.py scrape-once
```

### Option 3: Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Daily" and repeat every 15 minutes
4. Set action to run: `python main.py scrape-once`
5. Set start directory to your project folder

### Option 4: Docker (Advanced)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "run"]
```

### Option 5: systemd Service (Linux)
Create `/etc/systemd/system/yad2-scraper.service`:
```ini
[Unit]
Description=Yad2 Car Scraper
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/projectX
ExecStart=/usr/bin/python3 main.py run
Restart=always
Environment=TELEGRAM_BOT_TOKEN=your_token
Environment=TELEGRAM_CHAT_ID=your_chat_id

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable yad2-scraper
sudo systemctl start yad2-scraper
```

## File Structure 📁

```
projectX/
├── main.py                 # Main application and CLI
├── config.py               # Configuration settings
├── scraper.py              # Core scraping functionality  
├── telegram_bot.py         # Telegram notifications
├── manufacturer_mapper.py  # Manufacturer/model ID mapping
├── setup_telegram.py       # Telegram setup helper
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── data/                  # Created automatically
    ├── listings_cache.json    # Cache of seen listings
    ├── manufacturers.json     # Manufacturer ID mappings
    ├── models.json           # Model ID mappings  
    ├── user_filters.json     # Your custom filters
    └── *.log                 # Log files
```

## Example Usage 🎯

1. **Set up a filter for affordable Seat Ibiza cars:**
   ```bash
   python main.py add-filter
   # Name: "Affordable Seat Ibiza"
   # Manufacturer: 37 (Seat)
   # Model: 10507 (Ibiza)
   # Year: 2010-2018
   # KM: -1-120000
   # Price: 30000-80000
   ```

2. **Monitor multiple car types:**
   ```bash
   # Add filter for Toyota Corolla
   # Add filter for Honda Civic  
   # Add filter for any BMW under 100k km
   ```

3. **Start monitoring:**
   ```bash
   python main.py run
   ```

You'll receive Telegram notifications like:
```
🚗 New Car Listing Found!

📋 2015 Seat Ibiza 1.2 TSI Style
💰 Price: 65,000 ₪
📅 Year: 2015
🛣 Kilometers: 89,000
📍 Location: Tel Aviv

🔗 View Listing
```

## Troubleshooting 🔧

### Common Issues:

1. **No listings found**
   - Check if your filter parameters are too restrictive
   - Verify manufacturer/model IDs are correct
   - Run `python main.py scrape-once` to test

2. **Telegram notifications not working**
   - Run `python main.py test-telegram`
   - Verify bot token and chat ID
   - Make sure you've started a conversation with your bot

3. **Rate limiting/blocking**
   - The scraper includes delays and random user agents
   - If blocked, wait a few hours before retrying
   - Consider increasing `REQUEST_DELAY` in config.py

4. **Import errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.7+ recommended)

### Debug Mode:
Enable detailed logging by editing the logging level in `config.py` or `main.py`.

## Legal Notice ⚖️

This scraper is for personal use only. Please:
- Respect Yad2's terms of service
- Don't overload their servers
- Use reasonable delays between requests
- Consider the legal implications of web scraping in your jurisdiction

## Contributing 🤝

Feel free to submit issues, feature requests, or improvements!

## License 📄

This project is for educational and personal use only.