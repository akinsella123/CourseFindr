# CourseMatch: Intelligent University Course Discovery Platform

CourseMatch is an AI-powered platform that helps students discover suitable college courses based on their skills, interests, and career goals. The system uses advanced recommendation algorithms and natural language processing to provide personalized course suggestions.

## 🌟 Features

### Core Functionality
- **Intelligent Course Recommendations**: AI-powered matching based on skills, interests, and preferences
- **Skill Extraction**: NLP-based extraction of skills from free text descriptions
- **Advanced Filtering**: Filter by location, modality, tuition, duration, and more
- **PDF Export**: Generate professional course recommendation reports
- **CSV Import/Export**: Bulk course management for administrators

### Technical Features
- **RESTful API**: Comprehensive API with OpenAPI documentation
- **Real-time Recommendations**: Fast TF-IDF based similarity matching
- **Scalable Architecture**: Built with FastAPI and PostgreSQL
- **Search Suggestions**: Auto-completion for skills, interests, and locations
- **Analytics Dashboard**: Insights into recommendation patterns and course statistics

## 🏗️ Architecture

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **NLP**: spaCy for text processing
- **ML**: scikit-learn for recommendation algorithms
- **PDF Generation**: ReportLab
- **Caching**: Redis (optional)

### Key Components
- **Recommendation Engine**: TF-IDF vectorization with cosine similarity
- **Skill Extractor**: Multi-method NLP skill identification
- **PDF Generator**: Professional report generation
- **Course Management**: CRUD operations with CSV support

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd coursematch
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Manual Setup

1. **Prerequisites**
   ```bash
   # Install Python 3.11+
   # Install PostgreSQL 12+
   # Install Redis (optional)
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Database Setup**
   ```bash
   # Create database
   createdb coursematch
   
   # Run the application (tables will be created automatically)
   python -m app.main
   ```

5. **Start the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📊 Sample Data

Load sample course data to get started:

```bash
# Using the API endpoint
curl -X POST "http://localhost:8000/api/v1/courses/upload-csv" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@data/sample_courses.csv"
```

Or use the web interface at http://localhost:8000/docs

## 🔧 API Usage

### Get Course Recommendations

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/recommend" \
     -H "Content-Type: application/json" \
     -d '{
       "skills": ["Python", "Machine Learning"],
       "interests": ["Technology", "Data Science"],
       "location": "United States",
       "career_goals": "Data Scientist",
       "max_tuition": 50000
     }'
```

### Extract Skills from Text

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/extract-skills" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "I have experience with Python programming, machine learning, and data analysis. I enjoy working with databases and creating visualizations.",
       "context": "Software development background"
     }'
```

### Export Recommendations as PDF

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/recommend/export" \
     -H "Content-Type: application/json" \
     -d '{
       "skills": ["Python", "JavaScript"],
       "interests": ["Web Development"]
     }' \
     --output recommendations.pdf
```

## 📖 API Documentation

The complete API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/api/v1/openapi.json

### Main Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/v1/recommendations/recommend` | POST | Get course recommendations |
| `/api/v1/recommendations/extract-skills` | POST | Extract skills from text |
| `/api/v1/courses/` | GET | List courses with filtering |
| `/api/v1/courses/upload-csv` | POST | Bulk upload courses |
| `/api/v1/tags/skills` | GET | Get available skills |
| `/health` | GET | Health check |

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost/coursematch` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `DEBUG` | Enable debug mode | `false` |
| `SPACY_MODEL` | spaCy model name | `en_core_web_sm` |

### Database Configuration

The application automatically creates database tables on startup. For custom migrations, you can use Alembic:

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## 📈 Performance & Scaling

### Recommendations
- **Response Time**: < 200ms for typical queries
- **Throughput**: 100+ requests/second on modest hardware
- **Scalability**: Horizontal scaling with load balancers

### Optimization Features
- TF-IDF vectorization for fast similarity matching
- Database indexing on search fields
- Redis caching for frequent queries
- Background task processing for heavy operations

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## 🚢 Deployment

### Docker Deployment

```bash
# Build image
docker build -t coursematch .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  coursematch
```

### Cloud Deployment

The application is ready for deployment on:
- **Heroku**: Use the included `Dockerfile`
- **AWS ECS**: Container-ready with health checks
- **Google Cloud Run**: Serverless deployment
- **Azure Container Instances**: Simple container deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure all tests pass

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify credentials in .env file
```

**spaCy Model Not Found**
```bash
# Download the English model
python -m spacy download en_core_web_sm
```

**Import Errors**
```bash
# Ensure Python path is set
export PYTHONPATH=/path/to/coursematch
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **spaCy** for natural language processing capabilities
- **scikit-learn** for machine learning algorithms
- **PostgreSQL** for robust data storage
- **ReportLab** for PDF generation

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation at `/docs`
- Review the API examples above

---

**Built with ❤️ for students seeking their perfect educational path**