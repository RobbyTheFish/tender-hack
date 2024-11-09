import requests


class AuctionParser:
    def __init__(self, auction_id):
        self.auction_id = auction_id
        self.url = "https://zakupki.mos.ru/newapi/api/Auction/Get"
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        }
        self.params = {"auctionId": auction_id}
        self.auction_info = {}

    def _send_request(self):
        """
        Sends a request to the API to retrieve auction data.
        """
        response = requests.get(self.url, headers=self.headers, params=self.params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Request error: {response.status_code}")

    def _get_buyers_by_id(self, shared_purchase_buyers):
        """
        Создает словарь, где ключом является id покупателя, а значением — информация о нем.
        """
        buyers_dict = {}
        for buyer in shared_purchase_buyers:
            buyers_dict[buyer["id"]] = buyer
        return buyers_dict

    def _merge_buyers_with_deliveries(self, deliveries, buyers_dict):
        """
        Объединяет информацию о покупателе с каждой поставкой на основе buyerId.
        """
        for delivery in deliveries:
            for item in delivery.get("items", []):
                buyer_id = item.get("buyerId")
                if buyer_id in buyers_dict:
                    item["buyer_info"] = buyers_dict[buyer_id]
                else:
                    item["buyer_info"] = None  # Если покупатель не найден
        return deliveries

    def parse_data(self):
        """
        Parses API response and organizes auction data.
        """
        data = self._send_request()

        shared_purchase_buyers = data.get("sharedPurchaseBuyers", [])
        buyers_dict = self._get_buyers_by_id(shared_purchase_buyers)
        deliveries = data.get("deliveries", [])

        merged_deliveries = self._merge_buyers_with_deliveries(deliveries, buyers_dict)

        # Extract key auction data
        self.auction_info = {
            # Наименования закупки
            "name_category_auction": data.get("name"),
            # Обеспечание контракта
            "is_contract_guarantee_req": data.get("isContractGuaranteeRequired"),
            "contract_guarantee_amount": data.get("contractGuaranteeAmount"),
            # Проверка наличия сертификатов\лицензий
            "is_license_production": data.get("isLicenseProduction"),
            # График поставки и этап поставки
            "deliveries": merged_deliveries,
            # Максимальное значение цены или начальная цена
            "purchase_type_id": data.get(
                "purchaseTypeId"
            ),  # 1 - начальная цена; 2 - максимальное значение цены контракта
            # При наличии ТЗ: наименование и значение характеристики спецификаии закупки
        }

    def get_auction_info(self):
        """
        Returns auction information.
        """
        return self.auction_info

    def display_info(self):
        """
        Displays auction information in a structured format.
        """
        if not self.auction_info:
            print("Auction data has not been retrieved yet.")
            return

        print("Auction Information:")
        print(f"Name category action: {self.auction_info['name_category_auction']}")
        print(f"Created Customer {self.auction_info['created_by_customer']}")
        print(f"Customer: {self.auction_info['customer_name']}")
        print(f"Start Date: {self.auction_info['start_date']}")
        print(f"End Date: {self.auction_info['end_date']}")
        print(f"Start Cost: {self.auction_info['start_cost']}")
        print(f"State: {self.auction_info['auction_state']}")
        print(f"Federal Law: {self.auction_info['federal_law']}")

        print("\nItems:")
        for item in self.auction_info["items"]:
            print(f"- {item['id']}")
            print(f"- {item['name']}")
            print(f"  Cost per Unit: {item['currentValue']} {item['okeiName']}")
            print(f"  costPerUnit: {item['costPerUnit']}")

        print("Deliveries")
        print(self.auction_info["deliveries"])

        print("\nFiles:")
        for file in self.auction_info["files"]:
            print(f"- {file['name']} (ID: {file['id']})")
