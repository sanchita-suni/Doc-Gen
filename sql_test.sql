-- ============================================
-- E-Commerce Database Schema Demo
-- Comprehensive SQL example for parser testing
-- ============================================

-- ============================================
-- TABLES
-- ============================================

-- Customer information table
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    loyalty_points INT DEFAULT 0,
    is_premium BOOLEAN DEFAULT FALSE
);

/*
 * Product catalog table
 * Stores all available products with pricing and inventory
 */
CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    stock_quantity INT DEFAULT 0,
    reorder_level INT DEFAULT 10,
    supplier_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Order header table
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    shipping_address TEXT,
    billing_address TEXT,
    subtotal DECIMAL(10, 2),
    tax_amount DECIMAL(10, 2),
    shipping_cost DECIMAL(10, 2),
    total_amount DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

/*
 * Order line items table
 * Contains individual products within each order
 */
CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount_percent DECIMAL(5, 2) DEFAULT 0,
    line_total DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Supplier information
CREATE TABLE suppliers (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    rating DECIMAL(3, 2)
);

-- ============================================
-- STORED PROCEDURES
-- ============================================

/*
 * Get customer order history
 * Retrieves all orders for a specific customer with details
 */
CREATE PROCEDURE GetCustomerOrders(
    IN customerId INT,
    IN limitCount INT
)
BEGIN
    SELECT 
        o.order_id,
        o.order_date,
        o.total_amount,
        o.status,
        COUNT(oi.order_item_id) as item_count
    FROM orders o
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.customer_id = customerId
    GROUP BY o.order_id
    ORDER BY o.order_date DESC
    LIMIT limitCount;
END;

-- Add new customer to the system
CREATE PROCEDURE RegisterCustomer(
    IN firstName VARCHAR(50),
    IN lastName VARCHAR(50),
    IN emailAddress VARCHAR(100),
    IN phoneNumber VARCHAR(20)
)
BEGIN
    INSERT INTO customers (first_name, last_name, email, phone)
    VALUES (firstName, lastName, emailAddress, phoneNumber);
    
    SELECT LAST_INSERT_ID() as customer_id;
END;

/*
 * Process new order
 * Creates order header and returns order ID
 */
CREATE OR REPLACE PROCEDURE CreateOrder(
    IN customerId INT,
    IN shippingAddr TEXT,
    IN billingAddr TEXT,
    IN paymentMethod VARCHAR(50),
    OUT newOrderId INT
)
BEGIN
    INSERT INTO orders (customer_id, shipping_address, billing_address, payment_method)
    VALUES (customerId, shippingAddr, billingAddr, paymentMethod);
    
    SET newOrderId = LAST_INSERT_ID();
END;

-- Update product inventory after sale
CREATE PROCEDURE UpdateInventory(
    IN productId INT,
    IN quantitySold INT
)
BEGIN
    UPDATE products
    SET stock_quantity = stock_quantity - quantitySold,
        updated_at = CURRENT_TIMESTAMP
    WHERE product_id = productId;
    
    -- Check if reorder needed
    IF (SELECT stock_quantity FROM products WHERE product_id = productId) < 
       (SELECT reorder_level FROM products WHERE product_id = productId) THEN
        -- Log reorder alert (simplified)
        SELECT CONCAT('Reorder needed for product ', productId) as alert;
    END IF;
END;

/*
 * Apply discount to customer
 * Updates loyalty points and applies discount to order
 */
CREATE OR REPLACE PROCEDURE ApplyLoyaltyDiscount(
    IN customerId INT,
    IN orderId INT,
    IN pointsToUse INT
)
BEGIN
    DECLARE currentPoints INT;
    DECLARE discountAmount DECIMAL(10, 2);
    
    SELECT loyalty_points INTO currentPoints
    FROM customers
    WHERE customer_id = customerId;
    
    IF currentPoints >= pointsToUse THEN
        SET discountAmount = pointsToUse * 0.01; -- $0.01 per point
        
        UPDATE customers
        SET loyalty_points = loyalty_points - pointsToUse
        WHERE customer_id = customerId;
        
        UPDATE orders
        SET total_amount = total_amount - discountAmount
        WHERE order_id = orderId;
    END IF;
END;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Calculate order total with tax
CREATE FUNCTION CalculateOrderTotal(orderId INT) RETURNS DECIMAL(10, 2)
DETERMINISTIC
BEGIN
    DECLARE subtotal DECIMAL(10, 2);
    DECLARE taxRate DECIMAL(5, 4) DEFAULT 0.0825; -- 8.25% tax
    DECLARE shipping DECIMAL(10, 2) DEFAULT 9.99;
    DECLARE total DECIMAL(10, 2);
    
    SELECT SUM(line_total) INTO subtotal
    FROM order_items
    WHERE order_id = orderId;
    
    SET total = subtotal + (subtotal * taxRate) + shipping;
    RETURN total;
END;

/*
 * Get customer lifetime value
 * Calculates total amount spent by customer
 */
CREATE FUNCTION GetCustomerLifetimeValue(customerId INT) RETURNS DECIMAL(10, 2)
DETERMINISTIC
BEGIN
    DECLARE totalSpent DECIMAL(10, 2);
    
    SELECT COALESCE(SUM(total_amount), 0) INTO totalSpent
    FROM orders
    WHERE customer_id = customerId AND status = 'completed';
    
    RETURN totalSpent;
END;

-- Calculate product profit margin
CREATE FUNCTION CalculateProfitMargin(productId INT) RETURNS DECIMAL(5, 2)
DETERMINISTIC
BEGIN
    DECLARE productPrice DECIMAL(10, 2);
    DECLARE productCost DECIMAL(10, 2);
    DECLARE margin DECIMAL(5, 2);
    
    SELECT price, cost INTO productPrice, productCost
    FROM products
    WHERE product_id = productId;
    
    IF productCost > 0 THEN
        SET margin = ((productPrice - productCost) / productPrice) * 100;
    ELSE
        SET margin = 0;
    END IF;
    
    RETURN margin;
END;

/*
 * Check if product is available
 * Returns TRUE if product has sufficient stock
 */
CREATE OR REPLACE FUNCTION IsProductAvailable(
    productId INT,
    requestedQty INT
) RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    DECLARE availableStock INT;
    
    SELECT stock_quantity INTO availableStock
    FROM products
    WHERE product_id = productId;
    
    RETURN availableStock >= requestedQty;
END;

-- Get customer tier based on spending
CREATE FUNCTION GetCustomerTier(customerId INT) RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
    DECLARE lifetimeValue DECIMAL(10, 2);
    DECLARE tier VARCHAR(20);
    
    SET lifetimeValue = GetCustomerLifetimeValue(customerId);
    
    IF lifetimeValue >= 10000 THEN
        SET tier = 'Platinum';
    ELSEIF lifetimeValue >= 5000 THEN
        SET tier = 'Gold';
    ELSEIF lifetimeValue >= 1000 THEN
        SET tier = 'Silver';
    ELSE
        SET tier = 'Bronze';
    END IF;
    
    RETURN tier;
END;

-- ============================================
-- VIEWS
-- ============================================

-- Active customers view
CREATE VIEW active_customers AS
SELECT 
    customer_id,
    CONCAT(first_name, ' ', last_name) as full_name,
    email,
    phone,
    loyalty_points,
    is_premium,
    registration_date
FROM customers
WHERE customer_id IN (
    SELECT DISTINCT customer_id 
    FROM orders 
    WHERE order_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
);

/*
 * Low stock products view
 * Shows products that need reordering
 */
CREATE VIEW low_stock_products AS
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.stock_quantity,
    p.reorder_level,
    s.company_name as supplier,
    s.email as supplier_email
FROM products p
LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
WHERE p.stock_quantity <= p.reorder_level;

-- Order summary view
CREATE OR REPLACE VIEW order_summary AS
SELECT 
    o.order_id,
    o.order_date,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    c.email as customer_email,
    COUNT(oi.order_item_id) as total_items,
    o.subtotal,
    o.tax_amount,
    o.shipping_cost,
    o.total_amount,
    o.status
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id;

/*
 * Product sales performance view
 * Aggregates sales data by product
 */
CREATE VIEW product_sales_performance AS
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    COUNT(oi.order_item_id) as times_ordered,
    SUM(oi.quantity) as total_quantity_sold,
    SUM(oi.line_total) as total_revenue,
    AVG(oi.unit_price) as average_price,
    p.stock_quantity as current_stock
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id;

-- Monthly revenue view
CREATE OR REPLACE VIEW monthly_revenue AS
SELECT 
    DATE_FORMAT(order_date, '%Y-%m') as month,
    COUNT(order_id) as total_orders,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as average_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM orders
WHERE status = 'completed'
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month DESC;

/*
 * Customer purchase frequency view
 * Shows how often customers make purchases
 */
CREATE VIEW customer_purchase_frequency AS
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    COUNT(o.order_id) as total_orders,
    MIN(o.order_date) as first_order_date,
    MAX(o.order_date) as last_order_date,
    DATEDIFF(MAX(o.order_date), MIN(o.order_date)) as customer_lifetime_days,
    SUM(o.total_amount) as lifetime_value
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id
HAVING COUNT(o.order_id) > 0;

-- Made with Bob