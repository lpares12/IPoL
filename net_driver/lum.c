#ifndef LUM_DRIVER
#define LUM_DRIVER

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/netdevice.h>
#include <linux/if_arp.h>
#include <linux/if.h>


#define LUM_MTU 20
#define LUM_HDR_LEN 2
#define LUM_ADDR_LEN 0

struct lum_packet {
	struct lum_packet *next;
	struct net_device *dev;
	int datalen;
	u8 data[LUM_MTU];
};

struct lum_priv {
	struct net_device_stats stats;
	int status;
	struct sk_buff *skb;

	struct net_device *dev;
};

// METHODS
static int lum_open(struct net_device *dev) {
	printk("lum_open is called\n");
	return 0;
}

static int lum_stop(struct net_device *dev) {
	printk("lum_stop is called\n");
	return 0;
}

static int lum_start_xmit(struct sk_buff *skb, struct net_device *dev) {
	printk("lum_start_xmit is called\n");
	return 0;
}

static struct net_device_stats* lum_get_stats(struct net_device *dev) {
	struct lum_priv *priv;
	printk("lum_get_stats is called\n");
	priv = netdev_priv(dev);
	return &priv->stats;
}

static int lum_header(struct sk_buff *skb, struct net_device *dev,
						unsigned short type, const void *daddr, const void *saddr,
						unsigned len)
{
	printk("lum_header is called\n");
	return 0;
}

// Structs
static const struct header_ops lum_header_ops = {
	.create = lum_header
};

static const struct net_device_ops lum_device_ops = {
	.ndo_open = lum_open,
	.ndo_stop = lum_stop,
	.ndo_start_xmit = lum_start_xmit,
	.ndo_get_stats = lum_get_stats
};
//

// INIT METHODS
static void lum_init(struct net_device *dev)
{
	struct lum_priv *priv;

	printk("Entering lum_init\n");

	dev->netdev_ops = &lum_device_ops;
	dev->header_ops = &lum_header_ops;

	dev->type = ARPHRD_VOID; // defined in <linux/if_arp.h> NO SÉ QUE POSAR!! point-to-point
	dev->hard_header_len = LUM_HDR_LEN;
	dev->addr_len = LUM_ADDR_LEN;
	dev->mtu = LUM_MTU;
	dev->tx_queue_len = 10;

	//dev->broadcast[0] = 0; // no se que posar
	//dev->dev_addr = 0; // device physical address

	dev->flags = 0;
	dev->flags = IFF_NOARP | IFF_POINTOPOINT;

	dev->features = 0; // tema fragmentacio, checksums,...

	priv = netdev_priv(dev);
	memset(priv, 0, sizeof(struct lum_priv));

	printk("Exiting lum_init\n");
}

static struct net_device *lum_dev;

int lum_init_module(void)
{
	printk("Entering lum_init_module\n");

	lum_dev = alloc_netdev(sizeof(struct lum_priv), "lum%d", NET_NAME_UNKNOWN, lum_init);
	if(lum_dev == NULL) {
		printk("LUM device not initialized\n");
		return 0;
	}

	if(register_netdev(lum_dev))
	{
		printk("Error registering the device\n");
		//lum_cleanup();
		return 0;
	}

	printk("Exiting lum_init_module\n");
	return 0;
}

//

void lum_cleanup_module(void)
{
	printk("Cleaning lum module\n");
	unregister_netdev(lum_dev);
	free_netdev(lum_dev);
	printk("Lum module cleaned\n");
	return;
}

module_init(lum_init_module);
module_exit(lum_cleanup_module);

MODULE_AUTHOR("Lluc Pares");
MODULE_DESCRIPTION("Driver for IP over Light Emiting Diodes");
MODULE_LICENSE("MIT");

#endif // LUM_DRIVER