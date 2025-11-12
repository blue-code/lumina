#!/usr/bin/env python3
"""
동시성 테스트 스크립트
여러 스레드에서 동시에 프로젝트 매니저에 접근하여 thread-safety를 검증합니다.
"""

import threading
import time
from core.project_manager import ProjectManager
from models.request_model import RequestModel, HttpMethod


def test_concurrent_reads(pm: ProjectManager, thread_id: int, iterations: int = 100):
    """동시 읽기 테스트"""
    for i in range(iterations):
        requests = pm.get_all_requests()
        project_dict = pm.to_dict()
        if i % 20 == 0:
            print(f"Thread {thread_id}: Read iteration {i}, found {len(requests)} requests")


def test_concurrent_writes(pm: ProjectManager, thread_id: int, iterations: int = 50):
    """동시 쓰기 테스트"""
    for i in range(iterations):
        req = RequestModel(f"Request from Thread {thread_id} - {i}")
        req.method = HttpMethod.GET
        req.url = f"https://api.example.com/test/{thread_id}/{i}"
        pm.root_folder.add_request(req)
        if i % 10 == 0:
            print(f"Thread {thread_id}: Write iteration {i}")


def test_concurrent_search(pm: ProjectManager, thread_id: int, iterations: int = 100):
    """동시 검색 테스트"""
    for i in range(iterations):
        requests = pm.get_all_requests()
        if requests:
            # 첫 번째 요청 검색
            first_req = requests[0]
            found = pm.find_request_by_id(first_req.id)
            if found is None:
                print(f"Thread {thread_id}: ERROR - Request not found!")
        if i % 20 == 0:
            print(f"Thread {thread_id}: Search iteration {i}")


def test_mixed_operations(pm: ProjectManager, thread_id: int, iterations: int = 50):
    """읽기/쓰기 혼합 테스트"""
    for i in range(iterations):
        # 읽기
        requests = pm.get_all_requests()

        # 쓰기
        if i % 2 == 0:
            req = RequestModel(f"Mixed Thread {thread_id} - {i}")
            req.url = f"https://api.example.com/mixed/{thread_id}/{i}"
            pm.root_folder.add_request(req)

        # 검색
        if requests:
            pm.find_request_by_id(requests[0].id)

        if i % 10 == 0:
            print(f"Thread {thread_id}: Mixed iteration {i}")


def run_concurrency_test():
    """메인 동시성 테스트"""
    print("=" * 60)
    print("Lumina 동시성 테스트 시작")
    print("=" * 60)

    # 프로젝트 매니저 초기화
    pm = ProjectManager()
    pm.create_sample_project()

    initial_count = len(pm.get_all_requests())
    print(f"\n초기 요청 개수: {initial_count}")

    # 테스트 1: 동시 읽기
    print("\n[테스트 1] 동시 읽기 (10개 스레드)")
    threads = []
    for i in range(10):
        t = threading.Thread(target=test_concurrent_reads, args=(pm, i, 50))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"✓ 동시 읽기 완료. 현재 요청 개수: {len(pm.get_all_requests())}")

    # 테스트 2: 동시 쓰기
    print("\n[테스트 2] 동시 쓰기 (5개 스레드)")
    threads = []
    for i in range(5):
        t = threading.Thread(target=test_concurrent_writes, args=(pm, i, 20))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    final_count = len(pm.get_all_requests())
    expected_count = initial_count + (5 * 20)
    print(f"✓ 동시 쓰기 완료. 현재 요청 개수: {final_count}")
    print(f"  예상 개수: {expected_count}, 실제 개수: {final_count}")

    if final_count == expected_count:
        print("  ✓ 모든 쓰기 작업이 올바르게 처리되었습니다!")
    else:
        print(f"  ✗ 경고: 예상 개수와 다릅니다! (차이: {expected_count - final_count})")

    # 테스트 3: 동시 검색
    print("\n[테스트 3] 동시 검색 (10개 스레드)")
    threads = []
    for i in range(10):
        t = threading.Thread(target=test_concurrent_search, args=(pm, i, 50))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"✓ 동시 검색 완료")

    # 테스트 4: 혼합 작업
    print("\n[테스트 4] 혼합 작업 (읽기/쓰기/검색, 10개 스레드)")
    before_count = len(pm.get_all_requests())
    threads = []
    for i in range(10):
        t = threading.Thread(target=test_mixed_operations, args=(pm, i, 30))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    after_count = len(pm.get_all_requests())
    added = after_count - before_count
    print(f"✓ 혼합 작업 완료. 추가된 요청: {added}")
    print(f"  최종 요청 개수: {after_count}")

    # 테스트 5: 파일 저장 동시성
    print("\n[테스트 5] 동시 파일 저장 (5개 스레드)")

    def save_project(pm, thread_id):
        try:
            pm.save_to_file(f"test_project_{thread_id}.json")
            print(f"Thread {thread_id}: 저장 완료")
        except Exception as e:
            print(f"Thread {thread_id}: 저장 실패 - {e}")

    threads = []
    for i in range(5):
        t = threading.Thread(target=save_project, args=(pm, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"✓ 동시 파일 저장 완료")

    # 정리
    import os
    for i in range(5):
        try:
            os.remove(f"test_project_{i}.json")
        except:
            pass

    print("\n" + "=" * 60)
    print("✓ 모든 동시성 테스트 완료!")
    print("=" * 60)
    print(f"\n최종 통계:")
    print(f"  - 최종 요청 개수: {len(pm.get_all_requests())}")
    print(f"  - 프로젝트 이름: {pm.project_name}")
    print(f"  - 환경 개수: {len(pm.env_manager.environments)}")


if __name__ == '__main__':
    run_concurrency_test()
