"""HTML email templates."""


class EmailTemplates:
    @staticmethod
    def order_confirmation(order_data: dict) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; }}
            .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .order-details {{ background: #f9fafb; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
            .total {{ font-weight: bold; font-size: 18px; margin-top: 15px; }}
            .footer {{ background: #f9fafb; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
        </style></head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Order Confirmed!</h1>
                </div>
                <div class="content">
                    <p>Thank you for your order.</p>
                    <div class="order-details">
                        <p><strong>Order #:</strong> {order_data.get('order_number', '')}</p>
                        <p><strong>Type:</strong> {order_data.get('order_type', 'dine_in')}</p>
                        <p><strong>Items:</strong></p>
                        {''.join(f'<div class="item"><span>{i.get("item_name", "")} x{i.get("quantity", 1)}</span><span>₹{i.get("total", 0):.2f}</span></div>' for i in order_data.get('items', []))}
                        <div class="total">Total: ₹{order_data.get('total', 0):.2f}</div>
                    </div>
                </div>
                <div class="footer">
                    <p>Powered by KitchenOS</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def order_ready(order_data: dict) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; }}
            .header {{ background: #16a34a; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; text-align: center; }}
            .order-number {{ font-size: 24px; font-weight: bold; color: #16a34a; }}
        </style></head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Order is Ready!</h1>
                </div>
                <div class="content">
                    <div class="order-number">#{order_data.get('order_number', '')}</div>
                    <p>Please collect your order.</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def welcome(user_name: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; }}
            .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
        </style></head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to KitchenOS!</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>Welcome to KitchenOS Restaurant Management Platform.</p>
                    <p>Your account has been created successfully.</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def feedback_request(order_number: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; }}
            .header {{ background: #8b5cf6; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; text-align: center; }}
            .stars {{ font-size: 32px; margin: 20px 0; }}
        </style></head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>How was your experience?</h1>
                </div>
                <div class="content">
                    <p>We hope you enjoyed your meal!</p>
                    <p>Order #{order_number}</p>
                    <div class="stars">⭐⭐⭐⭐⭐</div>
                    <p>Your feedback helps us improve.</p>
                </div>
            </div>
        </body>
        </html>
        """
