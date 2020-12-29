# Home-Depot-web-scraper
Scraper for extracting following products' data from [homedepot.com](https://www.homedepot.com) for following categories:

Department | Sub department | Brands
--- | --- | ---
Appliances | Dishwashers | LG, Samsung
Appliances | Refrigerators | GE, Whirlpool
Decor & furniture | Bedroom furniture -> Mattresses | Sealy

## Project structure
* `spiders/produts` - spider for crawling through website
* `items` - contains ProductItem storing product's data
* `middlewares` - default generated scrapy code
* `pipelines` - contains SaveProductsPipeline for saving each product to .json file
* `settings` - global settings data

## Setup
```
git clone https://github.com/mtkublin/Home-Depot-web-scraper.git
cd Home-Depot-web-scraper
pip install -r requirements.txt
```

## Usage
#### Basic usage
To use install requirements and run: `scrapy crawl products` in the project's directory. 
Result files will be accessible in **results** folder.

#### Adding brands/departments
To add departments or brands you need to modify `BRANDS` variable in `settings.py`. 

Each object in `BRANDS` has following structure:

```
"dishwashers": {
    "base_path": "b/Appliances-Dishwashers",
    "nav_param": "N-5yc1vZc3po",
    "brands": [
        "LG-Electronics",
        "Samsung"
    ]
},
```

In this example:
* `dishwashers` - name of sub department
* `base_path` - base path in sub department page's url
* `nav_param` - id in sub department page's url (last element)
* `brands` - list of brand name strings (have to be in the same format as in brand page's 
url, i.e. `LG` needs to be `LG-Electronics`)

To scrape data for an additional brand add its name in a specific `"brands"` list.

To scrape data for additional department/sub department add another key-value pair 
in `BRANDS`, following above schema.

## TODOs
* Modify pipeline so that items are saved to database instead of files
* Analyze each product type's features to unify them
* Create item objects for each product type instead of one generic ProductItem class