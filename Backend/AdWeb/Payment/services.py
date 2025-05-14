from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from .models import Transaction
from Users.models import User
from AdPlace.models import Ad
from DataShow.models import DailyStats
from Users.models import Notification

class PaymentService:
    # 计费标准
    IMPRESSION_COST = Decimal('0.01')  # 每次展示0.01元
    CLICK_COST = Decimal('0.10')       # 每次点击0.10元
    PREPAYMENT_RATIO = Decimal('0.10') # 预扣10%
    BUDGET_WARNING_RATIO = Decimal('0.80')  # 预算使用80%时发出预警

    @classmethod
    def create_ad_prepayment(cls, ad: Ad) -> Transaction:
        """创建广告时预扣费用"""
        amount = ad.budget * cls.PREPAYMENT_RATIO
        return Transaction.objects.create(
            user=ad.advertiser,
            amount=amount,
            transaction_type='ad_spend',
            status='completed',
            ad=ad,
            description=f'广告"{ad.name}"预扣费用'
        )

    @classmethod
    def record_impression(cls, ad: Ad, ip_address: str = None, user_agent: str = None) -> bool:
        """记录广告展示并计费"""
        try:
            # 检查广告状态、余额和预算
            if not cls._check_ad_status(ad):
                return False

            # 检查每日预算
            if not cls._check_daily_budget(ad):
                return False

            # 创建展示记录
            impression = ad.impressions.create(
                ip_address=ip_address,
                user_agent=user_agent,
                cost=cls.IMPRESSION_COST
            )

            # 扣除费用
            cls._deduct_cost(ad, cls.IMPRESSION_COST, f'广告"{ad.name}"展示费用')
            return True
        except Exception as e:
            print(f"记录展示失败: {str(e)}")
            return False

    @classmethod
    def record_click(cls, ad: Ad, impression_id: int = None, ip_address: str = None, user_agent: str = None) -> bool:
        """记录广告点击并计费"""
        try:
            # 检查广告状态、余额和预算
            if not cls._check_ad_status(ad):
                return False

            # 检查每日预算
            if not cls._check_daily_budget(ad):
                return False

            # 创建点击记录
            impression = None
            if impression_id:
                impression = ad.impressions.get(id=impression_id)
            
            click = ad.clicks.create(
                impression=impression,
                ip_address=ip_address,
                user_agent=user_agent,
                cost=cls.CLICK_COST
            )

            # 扣除费用
            cls._deduct_cost(ad, cls.CLICK_COST, f'广告"{ad.name}"点击费用')
            return True
        except Exception as e:
            print(f"记录点击失败: {str(e)}")
            return False

    @staticmethod
    def _check_ad_status(ad: Ad) -> bool:
        """检查广告状态和余额"""
        if ad.status != 'active':
            return False
        
        user = ad.advertiser
        if user.balance <= 0:
            ad.status = 'paused'
            ad.save()
            return False
        
        return True

    @classmethod
    def _check_daily_budget(cls, ad: Ad) -> bool:
        """检查每日预算"""
        today = timezone.now().date()
        
        # 获取今日花费
        daily_stats = DailyStats.objects.filter(
            ad=ad,
            date=today
        ).first()
        
        if daily_stats:
            today_spent = daily_stats.cost
        else:
            today_spent = Decimal('0')
        
        # 检查是否超过每日预算
        if ad.daily_limit and today_spent >= ad.daily_limit:
            ad.status = 'paused'
            ad.save()
            return False
        
        # 检查是否接近每日预算（预警）
        if ad.daily_limit and today_spent >= ad.daily_limit * cls.BUDGET_WARNING_RATIO:
            # 发送预算预警通知（仅发送一次，避免重复）
            Notification.objects.get_or_create(
                user=ad.advertiser,
                title=f'广告“{ad.name}”预算预警',
                content=f'您的广告“{ad.name}”今日预算已使用{today_spent}元，达到每日限额的80%。请关注账户余额和广告效果。',
                status='unread',
            )
        
        return True

    @staticmethod
    def _deduct_cost(ad: Ad, amount: Decimal, description: str) -> None:
        """扣除费用并记录交易"""
        user = ad.advertiser
        user.balance -= amount
        user.save()

        Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type='ad_spend',
            status='completed',
            ad=ad,
            description=description
        )

    @classmethod
    def get_ad_budget_status(cls, ad: Ad) -> dict:
        """获取广告预算状态"""
        today = timezone.now().date()
        
        # 获取今日花费
        daily_stats = DailyStats.objects.filter(
            ad=ad,
            date=today
        ).first()
        
        today_spent = daily_stats.cost if daily_stats else Decimal('0')
        
        # 获取总花费
        total_spent = Transaction.objects.filter(
            ad=ad,
            transaction_type='ad_spend',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # 计算预算使用比例
        daily_usage_ratio = (today_spent / ad.daily_limit * 100) if ad.daily_limit else 0
        total_usage_ratio = (total_spent / ad.budget * 100) if ad.budget else 0
        
        return {
            'today_spent': today_spent,
            'total_spent': total_spent,
            'daily_limit': ad.daily_limit,
            'total_budget': ad.budget,
            'daily_usage_ratio': daily_usage_ratio,
            'total_usage_ratio': total_usage_ratio,
            'is_daily_warning': daily_usage_ratio >= cls.BUDGET_WARNING_RATIO * 100,
            'is_total_warning': total_usage_ratio >= cls.BUDGET_WARNING_RATIO * 100
        } 