from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import datetime
from http import HTTPStatus
from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm
from .models import Item, OrderItem, Address, Payment, Coupon, Order, Refund


class TestModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username='Tester')
        item = Item.objects.create(
            title='first item',
            price=123.312,
            category='S',
            label='P',
            slug='first-item',
            description='first item text'
        )
        order_item = OrderItem.objects.create(
            user=user,
            ordered=False,
            item=item,
            quantity=2
        )
        address = Address.objects.create(
            user=user,
            street_address='Busby way',
            apartment_address='Old Trafford',
            country='Ukraine',
            zip='123456',
            address_type='B',
            default=False
        )
        payment = Payment.objects.create(
            stripe_charge_id='123123asdasd0',
            user=user,
            amount=23.312,
        )
        coupon = Coupon.objects.create(
            code='Test code',
            amount=13.2
        )
        order = Order.objects.create(
            user=user,
            ref_code='ref code',
            ordered_date=datetime.now(),
            ordered=True,
            shipping_address=address,
            billing_address=address,
            payment=payment,
            coupon=coupon,
            being_delivered=False,
            received=False,
            refund_requested=False,
            refund_granted=False,
        )
        order.items.add(order_item)
        Refund.objects.create(
            order=order,
            reason='Bad items',
            accepted=False,
            email='mezidiaofficial@gmail.com'
        )

    def test_item_content(self):
        item = Item.objects.get(id=1)
        self.assertEqual(item.title, 'first item', 'Title is not equal')
        self.assertEqual(item.price, 123.312, 'Price is not equal')
        self.assertEqual(item.category, 'S', 'Category is not equal')
        self.assertEqual(item.label, 'P', 'Label is not equal')
        self.assertEqual(item.slug, 'first-item', 'Slug is not equal')
        self.assertEqual(item.description, 'first item text', 'Description is not equal')

    def test_order_item_content(self):
        item = Item.objects.get(id=1)
        order_item = OrderItem.objects.get(id=1)
        self.assertEqual(order_item.user.username, 'Tester', 'User name is not equal')
        self.assertEqual(order_item.ordered, False, 'Ordered is not false')
        self.assertEqual(order_item.item, item, 'Item is not equal')
        self.assertEqual(order_item.quantity, 2, 'Quantity is not equal')

    def test_address_content(self):
        address = Address.objects.get(id=1)
        self.assertEqual(address.user.username, 'Tester', 'User name is not equal')
        self.assertEqual(address.street_address, 'Busby way', 'Street address is not false')
        self.assertEqual(address.apartment_address, 'Old Trafford', 'Apartment address is not equal')
        self.assertEqual(address.country, 'Ukraine', 'Country is not equal')
        self.assertEqual(address.zip, '123456', 'Zip-code is not equal')
        self.assertEqual(address.address_type, 'B', 'Address type is not equal')
        self.assertEqual(address.default, False, 'Default is not equal')

    def test_payment_content(self):
        payment = Payment.objects.get(id=1)
        self.assertEqual(payment.user.username, 'Tester', 'User name is not equal')
        self.assertEqual(payment.stripe_charge_id, '123123asdasd0', 'Stripe charge id is not false')
        self.assertEqual(payment.amount, 23.312, 'Amount is not equal')

    def test_coupon_content(self):
        coupon = Coupon.objects.get(id=1)
        self.assertEqual(coupon.code, 'Test code', 'Code is not equal')
        self.assertEqual(coupon.amount, 13.2, 'Amount is not equal')

    def test_order_content(self):
        order = Order.objects.get(id=1)
        address = Address.objects.get(id=1)
        payment = Payment.objects.get(id=1)
        coupon = Coupon.objects.get(id=1)
        self.assertEqual(order.user.username, 'Tester', 'User name is not equal')
        self.assertEqual(order.ref_code, 'ref code', 'Ref code is not equal')
        self.assertEqual(order.ordered, True, 'Ordered is not true')
        self.assertEqual(order.shipping_address, address, 'Shipping address is not equal')
        self.assertEqual(order.billing_address, address, 'Billing address is not equal')
        self.assertEqual(order.payment, payment, 'Payment is not equal')
        self.assertEqual(order.coupon, coupon, 'Coupon is not equal')
        self.assertEqual(order.being_delivered, False, 'Order must be not delivered')
        self.assertEqual(order.received, False, 'Order must be not received')
        self.assertEqual(order.refund_requested, False, 'Order refund must be not requested')
        self.assertEqual(order.refund_granted, False, 'Order refund must be not granted')

    def test_refund_content(self):
        refund = Refund.objects.get(id=1)
        order = Order.objects.get(id=1)
        self.assertEqual(refund.order, order, 'Order is not equal')
        self.assertEqual(refund.reason, 'Bad items', 'Reason is not equal')
        self.assertEqual(refund.accepted, False, 'Refund must be not accepted')
        self.assertEqual(refund.email, 'mezidiaofficial@gmail.com', 'Email is not equal')


class ViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Item.objects.create(
            title='first item',
            price=123.312,
            category='S',
            label='P',
            slug='first-item',
            description='first item text'
        )

    # def test_home_view(self):
    #     url = reverse('core:home')
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_order_summary_view(self):
        url = reverse('core:order-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_add_coupon_view(self):
        url = reverse('core:add-coupon')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_request_refund_view(self):
        url = reverse('core:request-refund')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_product_view(self):
        item = Item.objects.get(id=1)
        url = reverse('core:product', kwargs={'slug': item.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_add_to_cart_view(self):
        item = Item.objects.get(id=1)
        url = reverse('core:add-to-cart', kwargs={'slug': item.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_remove_from_cart_view(self):
        item = Item.objects.get(id=1)
        url = reverse('core:remove-from-cart', kwargs={'slug': item.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_remove_item_from_cart_view(self):
        item = Item.objects.get(id=1)
        url = reverse('core:remove-single-item-from-cart', kwargs={'slug': item.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)


class FormTests(TestCase):
    def test_checkout_form(self):
        data = {'shipping_address': 'Texas',
                'shipping_address2': 'New York City',
                'shipping_country': 'UA',
                'shipping_zip': 'test-zip',
                'billing_address': 'Krakov',
                'billing_address2': 'Oslo',
                'billing_country': 'US',
                'billing_zip': 'Billing zip',
                'same_billing_address': True,
                'set_default_shipping': False,
                'use_default_shipping': True,
                'set_default_billing': False,
                'use_default_billing': True,
                'payment_option': 'S'}
        form = CheckoutForm(data=data)
        self.assertTrue(form.is_valid())
        data['payment_option'] = 'C'
        form = CheckoutForm(data=data)
        self.assertFalse(form.is_valid())

    def test_coupon_form(self):
        data = {'code': 'code'}
        form = CouponForm(data=data)
        self.assertTrue(form.is_valid())
        data['field'] = 'field'
        del data['code']
        form = CouponForm(data=data)
        self.assertFalse(form.is_valid())

    def test_refund_form(self):
        data = {'ref_code': 'code', 'message': 'text', 'email': 'mezidiaofficial@gmail.com'}
        form = RefundForm(data=data)
        self.assertTrue(form.is_valid())
        data['email'] = 'text'
        form = RefundForm(data=data)
        self.assertFalse(form.is_valid())

    def test_payment_form(self):
        data = {'stripeToken': 'code', 'save': True, 'use_default': False}
        form = PaymentForm(data=data)
        self.assertTrue(form.is_valid())
