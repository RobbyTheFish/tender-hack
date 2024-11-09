import requests
from typing import Dict, Any

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
        self.files = {}
        self.auction_info = {}
        self.criteria_forms = []

    def _send_request(self) -> None:
        """
        Sends a request to the API to retrieve auction data.
        """
        response = requests.get(self.url, headers=self.headers, params=self.params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Request error: {response.status_code}")
        
    def _get_item(self, item_id: int) -> Any:
        """
        Получить подробную инфромацию о товаре
        """
        item_url = "https://zakupki.mos.ru/newapi/api/Auction/GetAuctionItemAdditionalInfo"
        item_params = {"itemId": item_id}
        response = requests.get(item_url, headers=self.headers, params=item_params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Request error: {response.status_code}")

    def _get_buyers_by_id(self, shared_purchase_buyers: Dict ) -> Dict[str|int, Any]:
        """
        Создает словарь, где ключом является id покупателя, а значением — информация о нем.
        """
        buyers_dict = {}
        for buyer in shared_purchase_buyers:
            buyers_dict[buyer["id"]] = buyer
        return buyers_dict

    def _merge_buyers_with_deliveries(self, deliveries: Dict, buyers_dict: Dict) -> Dict[str|int, Any]:
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
    
    def _datetype_string_formating(self, delivery: Dict) -> Dict[str|int, Any]:
        """
        Получение строк для сроков выполнения поставок
        """
        if delivery["periodDaysFrom"]:
            arrangement_string = "От {} до {} дней".format(
                delivery["periodDaysFrom"],
                delivery["periodDaysTo"]
            )
        else:
            arrangement_string = "C {} до {}".format(
                delivery["periodDateFrom"], 
                delivery["periodDateTo"]
            )
        return arrangement_string
    
    def _prepare_delivery(self) -> Dict[str|int, Any]:
        """
        Подготовка нужных полей для delivery
        """

        prepared_deliveries = []
        for delivery in self.auction_info["deliveries"]:
            prepared_delivery = {
                "Сроки доставки": self._datetype_string_formating(delivery),
                "Место доставки": delivery["deliveryPlace"],
                "Список товаров": [
                    {"quantity": item.get("quantity"), "name": item.get("name")}
                    for item in delivery.get("items", [])
                ]
            }
            prepared_deliveries.append(prepared_delivery)
        return prepared_deliveries
    
    def _prepare_specifications(self) -> Dict[str|int, Any]:
        """
        Подготовка items
        """
        """
        currentValue
        name
        item_info
        """
        prepared_specifications = []
        for specification in self.auction_info["specifications"]:
            prepared_specification = {
                "Количество товаров": specification["currentValue"],
                "Имя товара": specification["name"],
                "Характеристики": self._get_item(specification["id"]).get("characteristics")
            }
            prepared_specifications.append(prepared_specification)

        return prepared_specifications

    def _criteria_forming(self) -> None:
        """
        Forms dicts for condition requests
        """
        # Критерий 1.
        self.criteria_forms.append({
            "Название закупки": 
                self.auction_info["name_category_auction"]
            })

        # Критерий 2.
        if self.auction_info["is_contract_guarantee_req"]:
            is_guarantee_required = "Да"
        else:
            is_guarantee_required = "Нет"
        self.criteria_forms.append({
            "Требуется ли обеспечение исполнения контракта": is_guarantee_required
            })

        # Критерий 3. 
        if self.auction_info["is_license_production"]:
            is_license_required = "Да"
        else:
            is_license_required = "Нет"
        self.criteria_forms.append({
            "Требуется ли наличие сертификатов/лицензий": is_license_required
        })

        # Критерий 4.
        self.criteria_forms.append(self._prepare_delivery())

        # Критерий 5.
        purchase_type_dict = {
            1: "Указана начальная цена",
            2: "Указана максимальная цена"
        }
        self.criteria_forms.append({
            "Тип цены": purchase_type_dict[self.auction_info["purchase_type_id"]]
        })

        # Критерий 6.
        self.criteria_forms.append(self._prepare_specifications())

    def parse_data(self) -> None:
        """
        Parses API response and organizes auction data.
        """
        data = self._send_request()
        deliveries = data.get("deliveries", [])

        if data.get("organizingTypeId") == 2:
            shared_purchase_buyers = data.get("sharedPurchaseBuyers", [])
            buyers_dict = self._get_buyers_by_id(shared_purchase_buyers)
            deliveries = self._merge_buyers_with_deliveries(deliveries, buyers_dict)


        self.files = data.get("files")
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
            "deliveries": deliveries,
            # Максимальное значение цены или начальная цена
            "purchase_type_id": data.get(
                "purchaseTypeId"
            ),  # 1 - начальная цена; 2 - максимальное значение цены контракта
            # При наличии ТЗ: наименование и значение характеристики спецификаии закупки
            "specifications": data.get("items", [])
        }
        self._criteria_forming()

    def get_auction_info(self) -> Dict[str|int, Any]:
        """
        Returns auction information.
        """
        return self.auction_info
    
    def display_criteria_info(self, file: bool) -> None:
        if file:
            with open("report_criteria", "w") as f:
                for criteria in self.criteria_forms:
                    f.write("Данные для критерия:")
                    f.write(str(criteria))
                    f.write("\n")

        for criteria in self.criteria_forms:
            print("Данные для критерия:")
            print(criteria)
            print("\n")
        
urls = [
"https://zakupki.mos.ru/auction/9864533",
"https://zakupki.mos.ru/auction/9864708",
"https://zakupki.mos.ru/auction/9864771",
"https://zakupki.mos.ru/auction/9864863",
"https://zakupki.mos.ru/auction/9864870",
"https://zakupki.mos.ru/auction/9864884",
"https://zakupki.mos.ru/auction/9864977",
"https://zakupki.mos.ru/auction/9862417",
"https://zakupki.mos.ru/auction/9862374",
"https://zakupki.mos.ru/auction/9862366"
]

for url in urls:
    url_id = url.split("/")[-1]
    parser = AuctionParser(url_id)
    parser.parse_data()
