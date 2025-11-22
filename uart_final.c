#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <linux/slab.h>

#define DRIVER_NAME "rpi_uart_final"
#define DEVICE_NAME "rpi_uart"
#define CLASS_NAME "rpi_uart"

static int major_number;
static struct class* uart_class = NULL;
static struct device* uart_device = NULL;
static struct cdev uart_cdev;

static int uart_open(struct inode *inodep, struct file *filep)
{
    printk(KERN_INFO "UART_FINAL: App conectada - UART FISICO ACTIVO\n");
    return 0;
}

static int uart_release(struct inode *inodep, struct file *filep)
{
    printk(KERN_INFO "UART_FINAL: App desconectada\n");
    return 0;
}

static ssize_t uart_write(struct file *filep, const char __user *buffer, size_t len, loff_t *offset)
{
    struct file *uart_file;
    ssize_t ret;
    char *kbuf;
    loff_t pos = 0;
    
    if (len == 0) return 0;
    
    kbuf = kmalloc(len, GFP_KERNEL);
    if (!kbuf) return -ENOMEM;
    
    if (copy_from_user(kbuf, buffer, len)) {
        kfree(kbuf);
        return -EFAULT;
    }
    
    printk(KERN_INFO "UART_FINAL: App -> Driver: %zd bytes: %.*s\n", len, (int)len, kbuf);
    
    // ✅ ESCRIBIR AL UART FISICO REAL - SIN LOOPBACK
    uart_file = filp_open("/dev/ttyS0", O_WRONLY | O_NONBLOCK, 0);
    if (IS_ERR(uart_file)) {
        printk(KERN_ERR "UART_FINAL: Error abriendo UART fisico\n");
        kfree(kbuf);
        return PTR_ERR(uart_file);
    }
    
    ret = kernel_write(uart_file, kbuf, len, &pos);
    filp_close(uart_file, NULL);
    
    if (ret > 0) {
        printk(KERN_INFO "UART_FINAL: ✅ ENVIADO por GPIO14: %zd bytes\n", ret);
    } else {
        printk(KERN_ERR "UART_FINAL: ❌ Error enviando: %zd\n", ret);
    }
    
    kfree(kbuf);
    return len; // Éxito para la app
}

static ssize_t uart_read(struct file *filep, char __user *buffer, size_t len, loff_t *offset)
{
    // ✅ SOLO leer del UART físico, NO hacer loopback
    struct file *uart_file;
    ssize_t ret;
    char *kbuf;
    loff_t pos = 0;
    
    kbuf = kmalloc(len, GFP_KERNEL);
    if (!kbuf) return -ENOMEM;
    
    uart_file = filp_open("/dev/ttyS0", O_RDONLY | O_NONBLOCK, 0);
    if (IS_ERR(uart_file)) {
        kfree(kbuf);
        return 0; // No hay datos
    }
    
    ret = kernel_read(uart_file, kbuf, len, &pos);
    filp_close(uart_file, NULL);
    
    if (ret > 0) {
        printk(KERN_INFO "UART_FINAL: 📥 RECIBIDO de GPIO15: %zd bytes\n", ret);
        if (copy_to_user(buffer, kbuf, ret)) {
            kfree(kbuf);
            return -EFAULT;
        }
        kfree(kbuf);
        return ret;
    }
    
    kfree(kbuf);
    return 0; // No hay datos
}

static struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = uart_open,
    .release = uart_release,
    .read = uart_read,
    .write = uart_write,
};

static int __init uart_init(void)
{
    int ret;
    dev_t devno = 0;
    
    printk(KERN_INFO "========================================\n");
    printk(KERN_INFO "UART_FINAL: 🚀 DRIVER UART FISICO REAL\n");
    printk(KERN_INFO "UART_FINAL: ✅ GPIO14 -> Pico GPIO1\n");
    printk(KERN_INFO "UART_FINAL: ❌ SIN LOOPBACK INTERNO\n");
    printk(KERN_INFO "========================================\n");
    
    ret = alloc_chrdev_region(&devno, 0, 1, DEVICE_NAME);
    if (ret < 0) return ret;
    
    major_number = MAJOR(devno);
    
    cdev_init(&uart_cdev, &fops);
    uart_cdev.owner = THIS_MODULE;
    
    if ((ret = cdev_add(&uart_cdev, devno, 1)) < 0)
        goto fail_cdev;
    
    uart_class = class_create(DRIVER_NAME);
    if (IS_ERR(uart_class)) {
        ret = PTR_ERR(uart_class);
        goto fail_class;
    }
    
    uart_device = device_create(uart_class, NULL, devno, NULL, DEVICE_NAME);
    if (IS_ERR(uart_device)) {
        ret = PTR_ERR(uart_device);
        goto fail_device;
    }
    
    printk(KERN_INFO "UART_FINAL: Listo (major %d) - /dev/rpi_uart\n", major_number);
    return 0;

fail_device: class_destroy(uart_class);
fail_class: cdev_del(&uart_cdev);
fail_cdev: unregister_chrdev_region(devno, 1);
    return ret;
}

static void __exit uart_exit(void)
{
    dev_t devno = MKDEV(major_number, 0);
    device_destroy(uart_class, devno);
    class_destroy(uart_class);
    cdev_del(&uart_cdev);
    unregister_chrdev_region(devno, 1);
    printk(KERN_INFO "UART_FINAL: Driver descargado\n");
}

module_init(uart_init);
module_exit(uart_exit);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Driver UART Fisico Final - Sin loopback");