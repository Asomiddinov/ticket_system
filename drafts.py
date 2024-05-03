# For reg.:
# <div class="d-flex align-content-start flex-wrap">
#     <table class="table table-info">
#         <thead class="thead-dark">
#             <tr class="table-dark">
#                 <th scope="col">#</th>
#                 <th scope="col">Client</th>
#                 <th scope="col">Address</th>
#                 <th scope="col">Miqdor</th>
#                 <th scope="col">Mark</th>
#                 <th scope="col">Umumiy narx</th>
#                 <th scope="col">Pul birligi</th>
#                 <th scope="col">To'landi</th>
#                 <th scope="col">Qoldiq</th>
#                 <th scope="col">Haydovchi</th>
#                 <th scope="col">Date</th>
#                 <th scope="col">Ruxsat</th>
#             </tr>
#         </thead>
#         <tbody>
#             <tr>
#                 <th scope="row">1</th>
#                 <td>{{ client }}</td>
#                 <td>{{ address }}</td>
#                 <td>{{ quantity }}</td>
#                 <td>{{ mark }}</td>
#                 <td>{{ price }}</td>
#                 <td>{{ currency }}</td>
#                 <td>{{ paid }}</td>
#                 <td>{{ price - paid }}</td>
#                 <td>{{ driver }}</td>
#                 <td>{{ driver }}</td>
#                 <td>{{ approve }}</td>
#             </tr>
#         </tbody>
#     </table>
# </div>

# For coloring in layout.html:
# background-color: rgb(54, 89, 107);
import requests
from bs4 import BeautifulSoup


def get():
    orginfo = input("Type something about company>> ")
    url = f"https://uzorg.info/search/main/{orginfo}/"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find_all(attrs={"class": "mb-1"})
    for result in results:
        print(result.get_text())


while True:
    get()
