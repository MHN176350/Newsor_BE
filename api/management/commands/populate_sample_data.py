from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from api.models import UserProfile, News, Category, Tag, Notification
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Creating sample data...')
        
        # Create users
        users = self.create_users()
        
        # Create categories
        categories = self.create_categories()
        
        # Create tags
        tags = self.create_tags()
        
        # Create news articles
        news_articles = self.create_news(users, categories, tags)
        
        # Create notifications
        self.create_notifications(users, news_articles)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data:\n'
                f'- {len(users)} users\n'
                f'- {len(categories)} categories\n'
                f'- {len(tags)} tags\n'
                f'- {len(news_articles)} news articles\n'
                f'- Sample notifications'
            )
        )

    def clear_data(self):
        """Clear existing data"""
        Notification.objects.all().delete()
        News.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

    def create_users(self):
        """Create sample users with different roles"""
        users_data = [
            {
                'username': 'admin_user',
                'email': 'admin@newsor.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'bio': 'System administrator with full access to manage the platform.'
            },
            {
                'username': 'manager_john',
                'email': 'john.manager@newsor.com',
                'first_name': 'John',
                'last_name': 'Manager',
                'role': 'manager',
                'bio': 'Content manager responsible for reviewing and approving articles.'
            },
            {
                'username': 'writer_sarah',
                'email': 'sarah.writer@newsor.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'role': 'writer',
                'bio': 'Technology journalist with 5+ years of experience covering latest tech trends.'
            },
            {
                'username': 'writer_mike',
                'email': 'mike.writer@newsor.com',
                'first_name': 'Mike',
                'last_name': 'Davis',
                'role': 'writer',
                'bio': 'Sports reporter covering major league games and athlete interviews.'
            },
            {
                'username': 'writer_emma',
                'email': 'emma.writer@newsor.com',
                'first_name': 'Emma',
                'last_name': 'Wilson',
                'role': 'writer',
                'bio': 'Political correspondent reporting on government policies and elections.'
            },
            {
                'username': 'reader_alex',
                'email': 'alex.reader@newsor.com',
                'first_name': 'Alex',
                'last_name': 'Brown',
                'role': 'reader',
                'bio': 'Avid news reader interested in technology and business news.'
            },
            {
                'username': 'reader_jane',
                'email': 'jane.reader@newsor.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'role': 'reader',
                'bio': 'News enthusiast who enjoys reading about current events and lifestyle.'
            }
        ]

        users = []
        for user_data in users_data:
            # Check if user already exists
            if User.objects.filter(username=user_data['username']).exists():
                user = User.objects.get(username=user_data['username'])
            else:
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='password123',  # Simple password for demo
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )

            # Create or update profile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': user_data['role'],
                    'bio': user_data['bio'],
                    'is_verified': True
                }
            )
            if not created:
                profile.role = user_data['role']
                profile.bio = user_data['bio']
                profile.is_verified = True
                profile.save()

            users.append(user)

        return users

    def create_categories(self):
        """Create sample categories"""
        categories_data = [
            {'name': 'Technology', 'description': 'Latest technology news and innovations'},
            {'name': 'Sports', 'description': 'Sports news, scores, and athlete updates'},
            {'name': 'Politics', 'description': 'Political news and government updates'},
            {'name': 'Business', 'description': 'Business news, market updates, and economy'},
            {'name': 'Health', 'description': 'Health and medical news'},
            {'name': 'Science', 'description': 'Scientific discoveries and research'},
            {'name': 'Entertainment', 'description': 'Entertainment news and celebrity updates'},
            {'name': 'World', 'description': 'International news and global events'},
            {'name': 'Lifestyle', 'description': 'Lifestyle tips and cultural trends'},
            {'name': 'Education', 'description': 'Educational news and academic updates'}
        ]

        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'slug': slugify(cat_data['name'])
                }
            )
            categories.append(category)

        return categories

    def create_tags(self):
        """Create sample tags"""
        tags_data = [
            'AI', 'Machine Learning', 'Blockchain', 'Cryptocurrency', 'Cloud Computing',
            'Cybersecurity', 'Mobile Apps', 'Web Development', 'Data Science', 'IoT',
            'Football', 'Basketball', 'Soccer', 'Olympics', 'Tennis', 'Baseball',
            'Elections', 'Policy', 'Government', 'Democracy', 'International Relations',
            'Stock Market', 'Startups', 'Innovation', 'Economy', 'Finance',
            'Mental Health', 'Nutrition', 'Fitness', 'Medical Research', 'Healthcare',
            'Climate Change', 'Space Exploration', 'Renewable Energy', 'Environment',
            'Movies', 'Music', 'Celebrities', 'TV Shows', 'Gaming',
            'Travel', 'Food', 'Fashion', 'Culture', 'Social Media'
        ]

        tags = []
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'slug': slugify(tag_name)}
            )
            tags.append(tag)

        return tags

    def create_news(self, users, categories, tags):
        """Create sample news articles"""
        writers = [user for user in users if user.profile.role == 'writer']
        
        news_data = [
            {
                'title': 'Revolutionary AI Breakthrough Changes Everything',
                'excerpt': 'Scientists announce a major breakthrough in artificial intelligence that could revolutionize how we interact with technology.',
                'content': '''<p>In a groundbreaking development that promises to reshape the technological landscape, researchers at the Advanced AI Institute have announced a revolutionary breakthrough in artificial intelligence that could fundamentally change how we interact with technology in our daily lives.</p>

<p>The new AI system, dubbed "ContextAI," demonstrates unprecedented ability to understand and respond to complex human emotions and contextual nuances in conversation. Unlike previous AI models that relied heavily on pattern recognition, ContextAI can genuinely comprehend the subtleties of human communication, including sarcasm, cultural references, and emotional undertones.</p>

<h2>Key Features and Capabilities</h2>

<p>The research team, led by Dr. Maria Rodriguez, has developed an AI system with several remarkable capabilities:</p>

<ul>
<li><strong>Emotional Intelligence:</strong> The system can detect and respond appropriately to human emotions, adapting its communication style based on the user's emotional state.</li>
<li><strong>Cultural Awareness:</strong> ContextAI has been trained on diverse cultural datasets, enabling it to understand and respect cultural differences in communication.</li>
<li><strong>Real-time Learning:</strong> Unlike static AI models, this system continues to learn and adapt from each interaction, becoming more personalized over time.</li>
<li><strong>Multimodal Processing:</strong> The AI can process text, voice, images, and even body language to provide more comprehensive understanding.</li>
</ul>

<h2>Potential Applications</h2>

<p>The implications of this breakthrough extend far beyond simple chatbots. Industry experts predict applications in:</p>

<blockquote>
"This technology could revolutionize everything from customer service to healthcare, providing more empathetic and understanding AI companions that truly grasp human needs." - Dr. James Chen, AI Ethics Researcher
</blockquote>

<p>Healthcare professionals are particularly excited about the potential for AI-assisted therapy and patient care, where emotional understanding is crucial for effective treatment.</p>

<h2>Addressing Concerns</h2>

<p>While the breakthrough is promising, the research team has been careful to address potential ethical concerns. They've implemented robust privacy protections and established guidelines for responsible AI development.</p>

<p>The technology is expected to enter beta testing next quarter, with commercial applications potentially available within two years.</p>''',
                'category': 'Technology',
                'tags': ['AI', 'Machine Learning', 'Innovation'],
                'status': 'published',
                'featured_image_url': 'https://res.cloudinary.com/demo/image/upload/v1640123456/ai_breakthrough.jpg'
            },
            {
                'title': 'Championship Finals Set Record Viewership Numbers',
                'excerpt': 'The championship game broke all previous viewership records with over 50 million viewers tuning in worldwide.',
                'content': '''<p>Last night's championship finals made history not just for the spectacular gameplay, but for shattering all previous viewership records. With over 50 million viewers tuning in worldwide, the event became the most-watched sporting event of the decade.</p>

<p>The thrilling match between the defending champions and the underdog challengers kept audiences on the edge of their seats for nearly three hours of intense competition. Social media platforms experienced unprecedented activity, with fans sharing reactions and highlights in real-time.</p>

<h2>Record-Breaking Statistics</h2>

<p>The numbers speak for themselves:</p>

<ul>
<li>50.2 million total viewers across all platforms</li>
<li>35% increase from last year's finals</li>
<li>Peak viewership of 52.8 million during the final quarter</li>
<li>Streamed in 180 countries worldwide</li>
<li>15 million social media interactions during the event</li>
</ul>

<h2>The Game That Captivated the World</h2>

<p>What made this championship so compelling wasn't just the high stakes, but the incredible story of perseverance and teamwork that unfolded on the field. The underdog team, which barely made it to the playoffs, showed remarkable determination throughout the season.</p>

<blockquote>
"This was more than just a game. It was a testament to the power of believing in yourself and never giving up, no matter the odds." - Championship MVP Sarah Thompson
</blockquote>

<p>The match featured several record-breaking moments, including the fastest goal in championship history and a comeback that will be remembered for generations.</p>

<h2>Global Impact</h2>

<p>The championship's success extends beyond entertainment value. Economic analysts estimate the event generated over $2 billion in global economic activity, from advertising revenue to merchandise sales and tourism.</p>

<p>Sports venues worldwide reported increased interest in the sport, with youth enrollment programs seeing a 40% spike in registration following the championship.</p>''',
                'category': 'Sports',
                'tags': ['Football', 'Championship', 'Records'],
                'status': 'published',
                'featured_image_url': 'https://res.cloudinary.com/demo/image/upload/v1640123456/championship_finals.jpg'
            },
            {
                'title': 'New Climate Initiative Promises Carbon Neutrality',
                'excerpt': 'Government announces ambitious new climate initiative aimed at achieving carbon neutrality by 2030.',
                'content': '''<p>In a landmark announcement that signals a major shift in environmental policy, the government has unveiled an ambitious new climate initiative that promises to achieve carbon neutrality by 2030, a full decade ahead of previous targets.</p>

<p>The comprehensive plan, developed in collaboration with leading climate scientists and environmental economists, outlines a multi-faceted approach to dramatically reduce greenhouse gas emissions while stimulating economic growth in the green technology sector.</p>

<h2>Key Components of the Initiative</h2>

<p>The climate initiative encompasses several major areas:</p>

<ul>
<li><strong>Renewable Energy Transition:</strong> $500 billion investment in solar, wind, and hydroelectric infrastructure</li>
<li><strong>Transportation Revolution:</strong> Incentives for electric vehicle adoption and expansion of public transit</li>
<li><strong>Industrial Modernization:</strong> Support for businesses to adopt clean technologies and sustainable practices</li>
<li><strong>Carbon Capture Technology:</strong> Research and development of innovative carbon removal solutions</li>
<li><strong>Forest Conservation:</strong> Protection and restoration of natural carbon sinks</li>
</ul>

<h2>Economic Opportunities</h2>

<p>Far from being an economic burden, the initiative is projected to create millions of new jobs in emerging green industries. Economic modeling suggests the plan could:</p>

<blockquote>
"This initiative represents the greatest economic opportunity of our generation. We're not just fighting climate change – we're building the foundation for sustainable prosperity." - Environmental Secretary Dr. Lisa Park
</blockquote>

<p>The plan includes provisions for retraining workers from traditional energy sectors, ensuring a just transition that leaves no one behind.</p>

<h2>International Collaboration</h2>

<p>The initiative has already garnered support from international partners, with several countries expressing interest in adopting similar frameworks. Climate scientists worldwide have praised the ambitious timeline and comprehensive approach.</p>

<p>Implementation begins next month with the launch of pilot programs in select regions, followed by nationwide rollout over the next two years.</p>''',
                'category': 'Politics',
                'tags': ['Climate Change', 'Policy', 'Environment'],
                'status': 'published',
                'featured_image_url': 'https://res.cloudinary.com/demo/image/upload/v1640123456/climate_initiative.jpg'
            },
            {
                'title': 'Stock Market Reaches Historic High Amid Tech Surge',
                'excerpt': 'Major stock indices hit record levels as technology companies report exceptional quarterly earnings.',
                'content': '''<p>The stock market reached unprecedented heights today as major indices broke through previous records, driven primarily by exceptional performance in the technology sector. The surge comes as several major tech companies reported quarterly earnings that far exceeded analyst expectations.</p>

<p>The broad market rally reflects growing investor confidence in the economic recovery and the continued digital transformation across industries. Technology stocks led the charge, with several companies seeing double-digit gains in a single trading session.</p>

<h2>Market Performance Highlights</h2>

<p>Today's trading session delivered remarkable results:</p>

<ul>
<li>S&P 500 closed up 2.8% at a record high of 4,856</li>
<li>NASDAQ surged 3.5%, breaking the 15,000 barrier for the first time</li>
<li>Tech sector gained 4.2%, leading all major sectors</li>
<li>Trading volume exceeded average by 65%</li>
<li>Market capitalization increased by $800 billion in one day</li>
</ul>

<h2>Driving Forces Behind the Rally</h2>

<p>Several factors contributed to today's historic performance:</p>

<blockquote>
"The convergence of strong earnings, technological innovation, and renewed economic optimism has created a perfect storm for market growth." - Chief Market Strategist Robert Kim
</blockquote>

<p>Key drivers include:</p>

<ul>
<li>Better-than-expected quarterly earnings from major tech companies</li>
<li>Positive economic indicators suggesting sustained growth</li>
<li>Breakthrough innovations in artificial intelligence and clean energy</li>
<li>Increased adoption of digital services across all sectors</li>
</ul>

<h2>Looking Ahead</h2>

<p>While today's gains are impressive, financial experts urge caution and remind investors of the importance of diversification. The rapid rise has prompted discussions about market valuations and sustainability of current growth rates.</p>

<p>Analysts remain optimistic about long-term prospects, particularly in emerging technologies and sustainable business models that are reshaping the global economy.</p>''',
                'category': 'Business',
                'tags': ['Stock Market', 'Technology', 'Economy'],
                'status': 'published',
                'featured_image_url': 'https://res.cloudinary.com/demo/image/upload/v1640123456/stock_market_surge.jpg'
            },
            {
                'title': 'Medical Breakthrough Offers Hope for Rare Disease Patients',
                'excerpt': 'Researchers develop promising new treatment that could transform lives of patients with rare genetic disorders.',
                'content': '''<p>In a development that brings new hope to millions of patients worldwide, medical researchers have announced a groundbreaking treatment for rare genetic disorders that could revolutionize patient care and quality of life.</p>

<p>The innovative therapy, developed through a collaboration between leading medical institutions, targets the root cause of several rare diseases that have historically had limited treatment options. Early clinical trials show unprecedented success rates and minimal side effects.</p>

<h2>Revolutionary Treatment Approach</h2>

<p>The new treatment utilizes advanced gene therapy techniques to address genetic mutations at their source:</p>

<ul>
<li><strong>Precision Targeting:</strong> The therapy specifically targets affected genes without impacting healthy cells</li>
<li><strong>Minimally Invasive:</strong> Delivered through a simple injection rather than complex surgical procedures</li>
<li><strong>Long-lasting Effects:</strong> Single treatment potentially provides benefits for years</li>
<li><strong>Broad Application:</strong> Effective against multiple rare genetic conditions</li>
</ul>

<h2>Clinical Trial Results</h2>

<p>The Phase III clinical trials yielded remarkable results:</p>

<blockquote>
"We've seen patients who couldn't walk suddenly able to run, and families given hope where there was none before. This treatment has the potential to transform countless lives." - Dr. Rachel Martinez, Lead Researcher
</blockquote>

<p>Trial participants showed:</p>
<ul>
<li>85% improvement in primary disease symptoms</li>
<li>Significant enhancement in quality of life measures</li>
<li>No serious adverse reactions reported</li>
<li>Sustained benefits over 18-month follow-up period</li>
</ul>

<h2>Path to Approval</h2>

<p>The research team is working closely with regulatory agencies to expedite the approval process. Given the urgent need and promising results, the treatment may be available through expanded access programs within the next year.</p>

<p>Patient advocacy groups have welcomed the news, emphasizing the importance of continued research funding for rare diseases that affect smaller populations but cause significant suffering.</p>''',
                'category': 'Health',
                'tags': ['Medical Research', 'Gene Therapy', 'Healthcare'],
                'status': 'published',
                'featured_image_url': 'https://res.cloudinary.com/demo/image/upload/v1640123456/medical_breakthrough.jpg'
            },
            {
                'title': 'Space Mission Discovers Potentially Habitable Exoplanet',
                'excerpt': 'NASA\'s latest space mission has identified a potentially habitable exoplanet just 40 light-years from Earth.',
                'content': '''<p>In an extraordinary discovery that could reshape our understanding of life in the universe, NASA's latest deep space mission has identified a potentially habitable exoplanet located just 40 light-years from Earth.</p>

<p>The planet, designated Kepler-442c, exhibits characteristics remarkably similar to Earth, including the presence of liquid water, a stable atmosphere, and temperatures that could support life as we know it.</p>

<h2>Remarkable Planetary Characteristics</h2>

<p>Kepler-442c possesses several Earth-like qualities that make it a prime candidate for habitability:</p>

<ul>
<li><strong>Size and Mass:</strong> Approximately 1.2 times the size of Earth with similar gravitational pull</li>
<li><strong>Orbital Zone:</strong> Located in the "Goldilocks zone" where liquid water can exist</li>
<li><strong>Atmospheric Composition:</strong> Spectral analysis suggests oxygen and water vapor presence</li>
<li><strong>Stable Climate:</strong> Orbits a stable star similar to our Sun</li>
<li><strong>Magnetic Field:</strong> Evidence of protective magnetic field against cosmic radiation</li>
</ul>

<h2>Detection Methods and Technology</h2>

<p>The discovery was made possible through advanced space telescope technology and sophisticated analysis techniques:</p>

<blockquote>
"This discovery represents decades of technological advancement and international collaboration. We're literally looking at a world that could harbor life." - Dr. Alan Foster, Mission Director
</blockquote>

<p>The detection involved:</p>
<ul>
<li>Transit photometry to measure planetary size and orbit</li>
<li>Radial velocity measurements to determine mass</li>
<li>Atmospheric spectroscopy to analyze composition</li>
<li>Advanced computer modeling to predict surface conditions</li>
</ul>

<h2>Implications for Astrobiology</h2>

<p>This discovery has profound implications for our search for extraterrestrial life. The relatively close distance of 40 light-years makes Kepler-442c a prime target for future detailed study and potentially even interstellar missions.</p>

<p>Scientists are already planning follow-up observations using next-generation telescopes to search for biosignatures - chemical markers that could indicate the presence of life.</p>

<h2>Future Exploration Plans</h2>

<p>Several space agencies are now developing plans for more detailed study of Kepler-442c, including advanced telescope observations and theoretical interstellar probe missions that could reach the system within several decades using breakthrough propulsion technologies.</p>''',
                'category': 'Science',
                'tags': ['Space Exploration', 'Exoplanets', 'NASA'],
                'status': 'published',
                'featured_image_url': 'https://res.cloudinary.com/demo/image/upload/v1640123456/exoplanet_discovery.jpg'
            },
            {
                'title': 'Draft Article: Emerging Trends in Sustainable Architecture',
                'excerpt': 'Exploring innovative sustainable building practices that are reshaping modern architecture.',
                'content': '''<p>The architecture industry is undergoing a revolutionary transformation as sustainability becomes not just a trend, but a fundamental requirement for modern building design. Architects worldwide are embracing innovative practices that minimize environmental impact while maximizing efficiency and livability.</p>

<p>From bio-based materials to energy-positive buildings, the new wave of sustainable architecture is proving that environmental responsibility and aesthetic excellence can go hand in hand.</p>

<h2>Revolutionary Building Materials</h2>

<p>The foundation of sustainable architecture lies in the materials used:</p>

<ul>
<li><strong>Bio-concrete:</strong> Self-healing concrete that reduces maintenance and extends building life</li>
<li><strong>Bamboo Composites:</strong> Stronger than steel and completely renewable</li>
<li><strong>Recycled Plastics:</strong> Ocean plastic transformed into durable building components</li>
<li><strong>Living Materials:</strong> Structures that incorporate living organisms for air purification</li>
</ul>

<p>This article is currently in draft status and under development.</p>''',
                'category': 'Science',
                'tags': ['Architecture', 'Sustainability', 'Innovation'],
                'status': 'draft',
                'featured_image_url': None
            },
            {
                'title': 'Pending Review: The Future of Digital Education',
                'excerpt': 'How technology is transforming education and creating new learning opportunities.',
                'content': '''<p>The education sector is experiencing unprecedented transformation as digital technologies reshape how we learn, teach, and access knowledge. From virtual reality classrooms to AI-powered personalized learning, the future of education is being written today.</p>

<p>This comprehensive analysis examines the latest trends in educational technology and their potential impact on students, educators, and institutions worldwide.</p>

<h2>Key Technological Innovations</h2>

<p>Several breakthrough technologies are driving this educational revolution:</p>

<ul>
<li><strong>Virtual and Augmented Reality:</strong> Immersive learning experiences that bring abstract concepts to life</li>
<li><strong>Artificial Intelligence:</strong> Personalized learning paths adapted to individual student needs</li>
<li><strong>Blockchain Credentials:</strong> Secure, verifiable digital certificates and degrees</li>
<li><strong>Cloud Computing:</strong> Universal access to educational resources and collaboration tools</li>
</ul>

<p>This article is currently pending review by our editorial team.</p>''',
                'category': 'Education',
                'tags': ['Digital Learning', 'Education Technology', 'Innovation'],
                'status': 'pending',
                'featured_image_url': 'https://res.cloudinary.com/demo/image/upload/v1640123456/digital_education.jpg'
            }
        ]

        news_articles = []
        for i, article_data in enumerate(news_data):
            # Get random writer
            author = random.choice(writers)
            
            # Get category
            category = None
            for cat in categories:
                if cat.name == article_data['category']:
                    category = cat
                    break
            
            # Create slug from title
            base_slug = slugify(article_data['title'])
            slug = base_slug
            counter = 1
            while News.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Create article
            article = News.objects.create(
                title=article_data['title'],
                slug=slug,
                content=article_data['content'],
                excerpt=article_data['excerpt'],
                author=author,
                category=category,
                status=article_data['status'],
                featured_image=article_data.get('featured_image_url'),
                created_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                updated_at=timezone.now() - timedelta(days=random.randint(0, 5))
            )

            # Add tags
            article_tags = []
            for tag_name in article_data['tags']:
                for tag in tags:
                    if tag.name == tag_name:
                        article_tags.append(tag)
                        break
            
            if article_tags:
                article.tags.set(article_tags)

            news_articles.append(article)

        return news_articles

    def create_notifications(self, users, news_articles):
        """Create sample notifications"""
        managers = [user for user in users if user.profile.role in ['manager', 'admin']]

        # Create notifications for pending articles
        pending_articles = [article for article in news_articles if article.status == 'pending']
        
        for article in pending_articles:
            for manager in managers:
                Notification.objects.create(
                    recipient=manager,
                    sender=article.author,
                    notification_type='article_submitted',
                    title=f'New Article Submitted: {article.title}',
                    message=f'{article.author.get_full_name() or article.author.username} has submitted "{article.title}" for review.',
                    article=article,
                    created_at=timezone.now() - timedelta(hours=random.randint(1, 24))
                )

        # Create approval notifications for published articles
        published_articles = [article for article in news_articles if article.status == 'published']
        for article in published_articles[:3]:  # Just a few for demo
            if managers:
                Notification.objects.create(
                    recipient=article.author,
                    sender=random.choice(managers),
                    notification_type='article_approved',
                    title=f'Article Approved: {article.title}',
                    message=f'Your article "{article.title}" has been approved and published.',
                    article=article,
                    created_at=timezone.now() - timedelta(hours=random.randint(1, 48))
                )
