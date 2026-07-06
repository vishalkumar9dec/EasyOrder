/Users/vishalkumar/projects/swiggy_builder_prog [main]% python3 scripts/test_whatsapp_api.py --check-subscription --waba-id 27488993034053054

Checking WABA subscription for 27488993034053054...
Subscription info:
{
  "data": [
    {
      "whatsapp_business_api_data": {
        "link": "https://www.facebook.com/games/?app_id=823160707397760",
        "name": "easyorder",
        "id": "823160707397760"
      }
    },
    {
      "whatsapp_business_api_data": {
        "category": "Business",
        "link": "https://www.facebook.com/games/?app_id=2202427980234937",
        "name": "WA DevX Webhook Events 1P App",
        "id": "2202427980234937"
      }
    }
  ]
}



=========

How to "The WhatsApp Business Account was not subscribed to the EasyOrder app. It was
   only showing Meta's DevX webhook app in `/{waba-id}/subscribed_apps`."


==========

Next Implementation Steps:

1. Create a new app and test the flow again.
2. When a message is sent from the phone, the same should be visible in the UI as well.
3. The message from EasyOrder should be standard one, not a very long URL, but a HREF, the one which whatsapp sends in the order template.
4. Should I have an EasyOrder business account as well, just like Japser's Market? When user chats with that account, it fetches the data from the easyorder backend. so 2 ways to operate
  a. @ tag
  b. dedicated as usual business chat in whatsapp, a bot basically. some sample use cases:
    i. What was my last order?
    ii. When will my order arrive?
    iii. Share the order details in the group.
    iv. What are nearest best restaurant for chole bhature?
    v. What are the best upcoming offers?

5. Also, a new use case is, EasyOrder will be able to create a wishlist, or order's list. And then when the user thinks that all the items have been added, user will review and place the order through EasyOrder.
   1. @EasyOrder add vim bar to my house monthly order list. --> this is too long, it has to be simplified, a tag and the item. 
   Sample use case flow below:
      1. show me the today's wishlist. 
      2. Add these items in the cart, place the best offers.
      3. Once I review it, place the order for me. 
